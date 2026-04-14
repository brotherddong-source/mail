"""
승인/발송 파이프라인
검토자가 초안을 승인하면 실제 메일 발송
"""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.outlook.sender import MailSender
from app.domain.drafts.models import AuditLog, DraftResponse

logger = logging.getLogger(__name__)


class ApprovalService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def approve_and_send(
        self,
        draft_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        edited_body: str | None = None,
        use_ko: bool = True,
    ) -> str:
        """
        초안 승인 후 발송.
        edited_body: 검토자가 수정한 본문 (없으면 AI 생성본 사용)
        """
        draft = await self._get_draft(draft_id)
        if not draft:
            raise ValueError(f"초안을 찾을 수 없습니다: {draft_id}")
        if draft.approval_status != "pending":
            raise ValueError(f"이미 처리된 초안입니다: {draft.approval_status}")

        from datetime import datetime, timezone

        if edited_body:
            draft.reviewer_body = edited_body

        draft.approval_status = "approved"
        draft.reviewer_id = reviewer_id
        draft.reviewed_at = datetime.now(timezone.utc)
        self.db.add(draft)

        sender = MailSender(self.db, self.user_id)
        subject = await sender.send_approved_draft(draft, reviewer_id, use_ko=use_ko)

        log = AuditLog(
            actor_id=reviewer_id,
            action="draft_approved",
            resource_type="draft_response",
            resource_id=draft_id,
            detail={"subject": subject},
        )
        self.db.add(log)

        return subject

    async def reject(
        self,
        draft_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        reason: str = "",
    ) -> None:
        """초안 반려"""
        draft = await self._get_draft(draft_id)
        if not draft:
            raise ValueError(f"초안을 찾을 수 없습니다: {draft_id}")

        from datetime import datetime, timezone

        draft.approval_status = "rejected"
        draft.reviewer_id = reviewer_id
        draft.reviewed_at = datetime.now(timezone.utc)
        self.db.add(draft)

        log = AuditLog(
            actor_id=reviewer_id,
            action="draft_rejected",
            resource_type="draft_response",
            resource_id=draft_id,
            detail={"reason": reason},
        )
        self.db.add(log)

    async def _get_draft(self, draft_id: uuid.UUID) -> DraftResponse | None:
        result = await self.db.execute(
            select(DraftResponse)
            .options(selectinload(DraftResponse.source_mail))
            .where(DraftResponse.id == draft_id)
        )
        return result.scalar_one_or_none()
