from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ...v1.endpoints.lenders import logger  # reuse structured logger
from ....schemas.common import ResponseModel
from ....services.integration_runner import IntegrationRunner
from ....core.config import settings
import hashlib
import time
from typing import Optional


router = APIRouter()


_IDEMPOTENCY_CACHE: dict[str, float] = {}


def _check_api_key(x_api_key: Optional[str]) -> None:
    if not settings.EXTERNAL_API_KEYS:
        return
    if not x_api_key or x_api_key not in settings.EXTERNAL_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _check_idempotency(idempotency_key: Optional[str]) -> None:
    if not idempotency_key:
        return
    now = time.time()
    exp = _IDEMPOTENCY_CACHE.get(idempotency_key)
    if exp and exp > now:
        raise HTTPException(status_code=409, detail="Duplicate request")
    _IDEMPOTENCY_CACHE[idempotency_key] = now + settings.IDEMPOTENCY_TTL_SECONDS


@router.post("/lenders/{lender_id}/lead-submission", response_model=ResponseModel)
async def external_lead_submission(
    lender_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    try:
        _check_api_key(x_api_key)
        _check_idempotency(idempotency_key)
        runner = IntegrationRunner()
        result = await runner.run(db, lender_id, payload or {}, mode="live")
        return ResponseModel(message="Lead submission executed", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("External lead submission failed", lender_id=lender_id, error=str(e))
        raise HTTPException(status_code=500, detail="Lead submission failed")


