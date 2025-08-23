import socket
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....core.database import get_db
from ....models.lender import Lender
from ....models.integration import IntegrationSequence, Integration
from ....schemas.common import ResponseModel


router = APIRouter()


@router.get("/lenders/{lender_id}/preflight", response_model=ResponseModel)
async def preflight(lender_id: int, db: AsyncSession = Depends(get_db)):
    # DNS reachability and minimal config checks
    result = await db.execute(select(Lender).where(Lender.id == lender_id))
    lender = result.scalar_one_or_none()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    seq_result = await db.execute(
        select(IntegrationSequence).where(IntegrationSequence.lender_id == lender_id, IntegrationSequence.is_active == True)
    )
    seq = seq_result.scalar_one_or_none()
    if not seq:
        return ResponseModel(message="No active sequence", data={"dns": None, "errors": ["No active sequence configured"]})

    steps_result = await db.execute(select(Integration).where(Integration.parent_sequence_id == seq.id))
    steps = list(steps_result.scalars().all())

    errors = []
    host = None
    dns_ok = None
    if lender.base_url:
        try:
            from urllib.parse import urlparse
            u = urlparse(lender.base_url)
            host = u.hostname
            if host:
                socket.gethostbyname(host)
                dns_ok = True
            else:
                dns_ok = False
                errors.append("Invalid base_url hostname")
        except Exception:
            dns_ok = False
            errors.append("DNS resolution failed for base_url")

    # check minimal payload presence per step
    for idx, s in enumerate(steps):
        if s.http_method in ("POST", "PUT", "PATCH") and not ((s.request_schema or {}).get("template") or s.depends_on_fields or s.request_headers):
            errors.append(f"Step {idx+1} has no template/mappings/headers; body may be empty")

    return ResponseModel(message="Preflight", data={"dns": {"host": host, "ok": dns_ok}, "errors": errors})


