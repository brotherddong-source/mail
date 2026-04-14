import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.domain.mails.models import MailMessage
from app.domain.drafts.models import DraftResponse
from app.domain.cases.models import Case

router = APIRouter()


@router.get("")
async def list_mails(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(MailMessage).order_by(desc(MailMessage.received_at)).limit(limit)
    if status and status != "all":
        q = q.where(MailMessage.processing_status == status)

    result = await db.execute(q)
    mails = result.scalars().all()

    # 사건 정보 조회
    case_ids = [m.case_id for m in mails if m.case_id]
    cases = {}
    if case_ids:
        case_result = await db.execute(select(Case).where(Case.id.in_(case_ids)))
        cases = {c.id: c for c in case_result.scalars().all()}

    return [
        {
            "id": str(m.id),
            "graph_message_id": m.graph_message_id,
            "from_email": m.from_email,
            "from_name": m.from_name,
            "subject": m.subject,
            "received_at": m.received_at.isoformat() if m.received_at else None,
            "has_attachments": m.has_attachments,
            "case_id": str(m.case_id) if m.case_id else None,
            "case_number": cases[m.case_id].case_number if m.case_id and m.case_id in cases else None,
            "client_name": cases[m.case_id].client_name if m.case_id and m.case_id in cases else None,
            "requires_reply": m.requires_reply,
            "priority": m.priority,
            "ai_summary": m.ai_summary,
            "ai_classification": m.ai_classification,
            "processing_status": m.processing_status,
        }
        for m in mails
    ]


@router.get("/{mail_id}")
async def get_mail(mail_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MailMessage)
        .options(selectinload(MailMessage.draft_responses))
        .where(MailMessage.id == mail_id)
    )
    mail = result.scalar_one_or_none()
    if not mail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")

    case = None
    if mail.case_id:
        case_result = await db.execute(select(Case).where(Case.id == mail.case_id))
        case = case_result.scalar_one_or_none()

    return {
        "id": str(mail.id),
        "graph_message_id": mail.graph_message_id,
        "from_email": mail.from_email,
        "from_name": mail.from_name,
        "subject": mail.subject,
        "received_at": mail.received_at.isoformat() if mail.received_at else None,
        "has_attachments": mail.has_attachments,
        "case_id": str(mail.case_id) if mail.case_id else None,
        "case_number": case.case_number if case else None,
        "client_name": case.client_name if case else None,
        "requires_reply": mail.requires_reply,
        "priority": mail.priority,
        "ai_summary": mail.ai_summary,
        "ai_translation": mail.ai_translation,
        "ai_classification": mail.ai_classification,
        "processing_status": mail.processing_status,
        "body_text": mail.body_text,
        "body_html": mail.body_html,
        "to_emails": mail.to_emails or [],
        "cc_emails": mail.cc_emails or [],
        "drafts": [
            {
                "id": str(d.id),
                "generated_body_ko": d.generated_body_ko,
                "generated_body_en": d.generated_body_en,
                "reviewer_body": d.reviewer_body,
                "suggested_to": d.suggested_to or [],
                "suggested_cc": d.suggested_cc or [],
                "approval_status": d.approval_status,
                "created_at": d.created_at.isoformat(),
            }
            for d in (mail.draft_responses or [])
        ],
    }
