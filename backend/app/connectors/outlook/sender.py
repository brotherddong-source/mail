"""
메일 발송 서비스 (수동 승인 후에만 호출 가능)
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.outlook.client import get_graph_client
from app.domain.drafts.models import AuditLog, DraftResponse

logger = logging.getLogger(__name__)


class MailSender:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.client = get_graph_client()

    async def send_approved_draft(
        self,
        draft: DraftResponse,
        reviewer_id: uuid.UUID,
        use_ko: bool = True,
    ) -> str:
        """
        승인된 초안을 발송.
        MVP에서는 반드시 승인 상태(approved)인 초안만 처리.
        """
        if draft.approval_status != "approved":
            raise ValueError("승인되지 않은 초안은 발송할 수 없습니다.")

        body = draft.reviewer_body or (draft.generated_body_ko if use_ko else draft.generated_body_en)
        if not body:
            raise ValueError("발송할 본문이 없습니다.")

        to_list = draft.suggested_to or []
        cc_list = draft.suggested_cc or []

        source_mail = draft.source_mail
        subject = f"Re: {source_mail.subject}" if source_mail else "회신"

        await self.client.send_mail(
            user_id=self.user_id,
            subject=subject,
            body_html=body,
            to_recipients=to_list,
            cc_recipients=cc_list if cc_list else None,
            reply_to_message_id=source_mail.graph_message_id if source_mail else None,
        )

        # 발송 상태 업데이트
        from datetime import datetime, timezone
        draft.sent_at = datetime.now(timezone.utc)
        self.db.add(draft)

        # 감사 로그 기록
        log = AuditLog(
            actor_id=reviewer_id,
            action="mail_sent",
            resource_type="draft_response",
            resource_id=draft.id,
            detail={
                "subject": subject,
                "to": to_list,
                "cc": cc_list,
            },
        )
        self.db.add(log)
        await self.db.flush()

        logger.info("메일 발송 완료 (draft_id: %s)", draft.id)
        return subject
