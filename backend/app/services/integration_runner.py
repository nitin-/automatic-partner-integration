from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.lender import Lender
from ..models.integration import IntegrationSequence, Integration, IntegrationLog
from ..models.field_mapping import FieldMapping


def _join_url(base_url: str, endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    if not base_url:
        return endpoint
    if base_url.endswith('/') and endpoint.startswith('/'):
        return base_url[:-1] + endpoint
    if not base_url.endswith('/') and not endpoint.startswith('/'):
        return base_url + '/' + endpoint
    return base_url + endpoint


def _get_from_path(data: Dict[str, Any], path: str) -> Any:
    # Minimal $.a.b support
    if not path:
        return None
    p = path
    if p.startswith('$.'):
        p = p[2:]
    parts = [seg for seg in p.split('.') if seg]
    cur: Any = data
    for seg in parts:
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None
    return cur


def _set_to_path(data: Dict[str, Any], path: str, value: Any) -> None:
    if not path:
        return
    p = path
    if p.startswith('$.'):
        p = p[2:]
    parts = [seg for seg in p.split('.') if seg]
    cur: Any = data
    for seg in parts[:-1]:
        if seg not in cur or not isinstance(cur[seg], dict):
            cur[seg] = {}
        cur = cur[seg]
    if parts:
        cur[parts[-1]] = value


class IntegrationRunner:
    async def run(
        self,
        db: AsyncSession,
        lender_id: int,
        input_payload: Dict[str, Any],
        mode: str = "test",
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        lender = await self._get_lender(db, lender_id)
        sequence = await self._get_active_sequence(db, lender_id)
        if not sequence:
            return {"status": "no_sequence", "steps": [], "run_id": run_id}

        steps = await self._get_steps(db, sequence.id)
        field_mappings = await self._get_field_mappings(db, lender_id)

        previous_outputs: Dict[str, Any] = {}
        step_results: List[Dict[str, Any]] = []

        if sequence.execution_mode == "parallel":
            # Parallel execution disallows dependencies (validated earlier). Execute concurrently.
            async with httpx.AsyncClient(timeout=30.0) as client:
                tasks = [
                    self._execute_step(db, run_id, sequence, client, lender, s, field_mappings, input_payload, previous_outputs)
                    for s in steps
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    step_results.append({"error": str(res)})
                else:
                    step_results.append(res)
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for s in steps:
                    result = await self._execute_step(
                        db, run_id, sequence, client, lender, s, field_mappings, input_payload, previous_outputs
                    )
                    step_results.append(result)
                    # merge outputs for dependencies
                    if result.get("extracted_outputs"):
                        previous_outputs.update(result["extracted_outputs"])

        return {
            "status": "ok",
            "run_id": run_id,
            "sequence_id": sequence.id,
            "lender_id": lender_id,
            "steps": step_results,
        }

    async def _execute_step(
        self,
        db: AsyncSession,
        run_id: str,
        sequence: IntegrationSequence,
        client: httpx.AsyncClient,
        lender: Lender,
        step: Integration,
        field_mappings: List[FieldMapping],
        input_payload: Dict[str, Any],
        previous_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Build URL
        url = _join_url(lender.base_url, step.api_endpoint)

        # Build headers and auth
        headers: Dict[str, str] = {"Content-Type": "application/json", **(step.request_headers or {})}
        auth_cfg = step.auth_config or lender.auth_config or {}
        auth_type = (step.auth_type.value if hasattr(step.auth_type, 'value') else step.auth_type) or "none"
        if auth_type in ("bearer_token", "bearer"):
            token = auth_cfg.get("token") or auth_cfg.get("access_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            key_name = auth_cfg.get("key_name", "X-API-Key")
            key_value = auth_cfg.get("key_value") or auth_cfg.get("api_key")
            key_location = auth_cfg.get("key_location", "header")
            if key_value:
                if key_location == "header":
                    headers[key_name] = key_value
                elif key_location == "query":
                    # add to query params later when URL is constructed
                    pass
                elif key_location == "body":
                    # will be merged into request body below
                    pass
        elif auth_type in ("none", None, ""):
            # no auth headers
            pass

        # Build request body via field mappings and dependencies
        request_body: Dict[str, Any] = {}

        # Dependencies from previous steps
        for dest, source in (step.depends_on_fields or {}).items():
            value = previous_outputs.get(source)
            if value is not None:
                _set_to_path(request_body, dest, value)

        # Apply lender-level field mappings
        for m in field_mappings:
            value = _get_from_path(input_payload, m.source_field if m.source_field else "")
            if value is None:
                value = m.default_value if m.default_value is not None else value
            if value is None and m.fallback_value is not None:
                value = m.fallback_value
            if value is not None and m.target_field:
                _set_to_path(request_body, m.target_field, value)

        # Merge optional body template if provided in request_schema
        template = None
        if step.request_schema and isinstance(step.request_schema, dict):
            template = step.request_schema.get("template")
            # collect optional query params from schema
            schema_query_params = step.request_schema.get("query_params") or {}
        else:
            schema_query_params = {}
        if isinstance(template, dict):
            # shallow merge template first, then mappings override
            merged = dict(template)
            for k, v in request_body.items():
                merged[k] = v if not isinstance(v, dict) else {**(template.get(k, {}) if isinstance(template.get(k, {}), dict) else {}), **v}
            request_body = merged

        # Prepare query params and URL
        final_url = url
        try:
            parsed = urlparse(url)
            existing_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            # from schema
            query_params: Dict[str, Any] = {}
            if isinstance(schema_query_params, dict):
                for k, v in schema_query_params.items():
                    if v is not None:
                        query_params[str(k)] = str(v)
            # API key in query
            if auth_type == "api_key" and auth_cfg.get("key_location") == "query":
                key_name = auth_cfg.get("key_name", "api_key")
                key_value = auth_cfg.get("key_value") or auth_cfg.get("api_key")
                if key_value:
                    query_params[str(key_name)] = str(key_value)
            merged_params = {**existing_params, **query_params}
            new_query = urlencode(merged_params, doseq=True)
            final_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        except Exception:
            final_url = url

        # HTTP method
        method = (step.http_method or "POST").upper()

        # Timeouts/retries
        retries = max(0, int(step.retry_count or 0))
        delay = max(0, int(step.retry_delay_seconds or 0))

        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= retries:
            try:
                if method in ("GET", "DELETE"):
                    resp = await client.request(method, final_url, headers=headers, params=None)
                else:
                    # Add API key to body if configured so
                    if auth_type == "api_key" and auth_cfg.get("key_location") == "body":
                        key_name = auth_cfg.get("key_name", "api_key")
                        key_value = auth_cfg.get("key_value") or auth_cfg.get("api_key")
                        if key_value:
                            request_body[key_name] = key_value
                    resp = await client.request(method, final_url, headers=headers, json=request_body)
                data = None
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}

                extracted: Dict[str, Any] = {}
                for out in (step.output_fields or []):
                    val = _get_from_path(data if isinstance(data, dict) else {}, out)
                    if val is not None:
                        # use the jsonpath-like string as the key by default
                        extracted[out] = val

                # Persist log
                log = IntegrationLog(
                    integration_id=step.id,
                    sequence_id=sequence.id,
                    step_order=step.sequence_order,
                    request_id=run_id,
                    request_data=request_body,
                    request_headers=headers,
                    response_status=resp.status_code,
                    response_data=data if isinstance(data, dict) else {"raw": resp.text},
                    duration_ms=None,
                )
                db.add(log)
                await db.commit()

                return {
                    "step_id": step.id,
                    "name": step.name,
                    "url": final_url,
                    "status_code": resp.status_code,
                    "request": {"method": method, "headers": headers, "body": request_body},
                    "response": data,
                    "extracted_outputs": extracted,
                }
            except Exception as exc:  # network/timeouts
                last_exc = exc
                if attempt >= retries:
                    # Persist error log
                    log = IntegrationLog(
                        integration_id=step.id,
                        sequence_id=sequence.id,
                        step_order=step.sequence_order,
                        request_id=run_id,
                        request_data=request_body,
                        request_headers=headers,
                        response_status=None,
                        response_data={"error": str(exc)},
                    )
                    db.add(log)
                    await db.commit()

                    return {
                        "step_id": step.id,
                        "name": step.name,
                        "url": final_url,
                        "error": str(exc),
                        "request": {"method": method, "headers": headers, "body": request_body},
                    }
                await asyncio.sleep(delay)
                attempt += 1

        # Should not reach here
        return {"step_id": step.id, "name": step.name, "error": str(last_exc) if last_exc else "unknown"}

    async def _get_lender(self, db: AsyncSession, lender_id: int) -> Lender:
        result = await db.execute(select(Lender).where(Lender.id == lender_id))
        lender = result.scalar_one()
        return lender

    async def _get_active_sequence(self, db: AsyncSession, lender_id: int) -> Optional[IntegrationSequence]:
        result = await db.execute(
            select(IntegrationSequence).where(
                IntegrationSequence.lender_id == lender_id,
                IntegrationSequence.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _get_steps(self, db: AsyncSession, sequence_id: int) -> List[Integration]:
        result = await db.execute(
            select(Integration).where(Integration.parent_sequence_id == sequence_id).order_by(Integration.sequence_order.asc())
        )
        return list(result.scalars().all())

    async def _get_field_mappings(self, db: AsyncSession, lender_id: int) -> List[FieldMapping]:
        result = await db.execute(select(FieldMapping).where(FieldMapping.lender_id == lender_id))
        return list(result.scalars().all())


