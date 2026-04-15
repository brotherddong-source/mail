import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.workflow.approval import ApprovalService

router = APIRouter()

# 임시 reviewer_id (추후 인증 모듈 연결)
TEMP_REVIEWER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEMP_USER_ID = "me"  # Graph API user


class RecipientEdit(BaseModel):
    email: str
    name: str | None = None


class ApproveRequest(BaseModel):
    edited_body: str | None = None
    use_ko: bool = True
    edited_to: list[RecipientEdit] | None = None
    edited_cc: list[RecipientEdit] | None = None


class RejectRequest(BaseModel):
    reason: str = ""


@router.post("/{draft_id}/approve")
async def approve_draft(
    draft_id: uuid.UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, TEMP_USER_ID)
    try:
        subject = await service.approve_and_send(
            draft_id=draft_id,
            reviewer_id=TEMP_REVIEWER_ID,
            edited_body=body.edited_body,
            use_ko=body.use_ko,
            edited_to=[r.model_dump() for r in body.edited_to] if body.edited_to else None,
            edited_cc=[r.model_dump() for r in body.edited_cc] if body.edited_cc else None,
        )
        return {"status": "sent", "subject": subject}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/reject")
async def reject_draft(
    draft_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ApprovalService(db, TEMP_USER_ID)
    try:
        await service.reject(
            draft_id=draft_id,
            reviewer_id=TEMP_REVIEWER_ID,
            reason=body.reason,
        )
        return {"status": "rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
