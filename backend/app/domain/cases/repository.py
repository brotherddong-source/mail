import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.cases.models import Case, Party


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, case_id: uuid.UUID) -> Case | None:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        return result.scalar_one_or_none()

    async def get_by_case_number(self, case_number: str) -> Case | None:
        result = await self.db.execute(
            select(Case).where(Case.case_number == case_number)
        )
        return result.scalar_one_or_none()

    async def find_by_client_domain(self, domain: str) -> list[Case]:
        result = await self.db.execute(
            select(Case).where(Case.client_domain == domain.lower())
        )
        return list(result.scalars().all())

    async def find_by_party_email(self, email: str) -> list[Case]:
        result = await self.db.execute(
            select(Case)
            .join(Party, Party.case_id == Case.id)
            .where(Party.email == email.lower())
        )
        return list(result.scalars().all())

    async def find_recent_by_sender(self, from_email: str, limit: int = 5) -> list[Case]:
        """과거 동일 발신자가 연관된 사건 이력"""
        from sqlalchemy import func
        from app.domain.mails.models import MailMessage
        # DISTINCT + ORDER BY 충돌 방지: subquery로 최근 메일의 case_id 조회 후 join
        subq = (
            select(MailMessage.case_id, func.max(MailMessage.received_at).label("latest"))
            .where(
                MailMessage.from_email == from_email.lower(),
                MailMessage.case_id.isnot(None),
            )
            .group_by(MailMessage.case_id)
            .order_by(func.max(MailMessage.received_at).desc())
            .limit(limit)
            .subquery()
        )
        result = await self.db.execute(
            select(Case).join(subq, Case.id == subq.c.case_id)
        )
        return list(result.scalars().all())

    async def find_by_conversation(self, conversation_id: str) -> Case | None:
        """같은 conversation_id의 이전 메일에서 사건 찾기"""
        from app.domain.mails.models import MailMessage
        result = await self.db.execute(
            select(Case)
            .join(MailMessage, MailMessage.case_id == Case.id)
            .where(
                MailMessage.conversation_id == conversation_id,
                MailMessage.case_id.isnot(None),
            )
            .order_by(MailMessage.received_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
