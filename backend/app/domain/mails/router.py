import base64
import re
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.domain.mails.models import MailMessage, MailAttachment
from app.domain.drafts.models import DraftResponse
from app.domain.cases.models import Case

router = APIRouter()


@router.get("")
async def list_mails(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, description="제목/발신자/요약 검색"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(MailMessage).order_by(desc(MailMessage.received_at)).limit(limit)
    if status and status != "all":
        q = q.where(MailMessage.processing_status == status)
    if search:
        like = f"%{search}%"
        from sqlalchemy import or_
        q = q.where(
            or_(
                MailMessage.subject.ilike(like),
                MailMessage.from_email.ilike(like),
                MailMessage.from_name.ilike(like),
                MailMessage.ai_summary.ilike(like),
            )
        )

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
            "to_emails": m.to_emails or [],
            "cc_emails": m.cc_emails or [],
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
        "body_html": _rewrite_cid(mail.body_html, str(mail.id)) if mail.body_html else None,
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


# ── 인라인 이미지 프록시 ───────────────────────────────────────────
@router.get("/{mail_id}/inline/{content_id:path}")
async def get_inline_image(
    mail_id: uuid.UUID,
    content_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Outlook CID 인라인 이미지를 서빙.
    1) DB에 content_b64가 저장된 경우 → 즉시 반환
    2) graph_attachment_id가 있으면 Graph API에서 실시간 fetch
    """
    # DB에서 첨부 조회
    result = await db.execute(
        select(MailAttachment).where(
            MailAttachment.mail_id == mail_id,
            MailAttachment.content_id == content_id,
        )
    )
    att = result.scalar_one_or_none()

    if att and att.content_b64:
        data = base64.b64decode(att.content_b64)
        return Response(content=data, media_type=att.content_type or "image/png")

    if att and att.graph_attachment_id:
        # 메일 조회해서 graph_message_id 가져오기
        mail_result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
        mail = mail_result.scalar_one_or_none()
        if mail and mail.graph_message_id:
            try:
                from app.connectors.outlook.graph_client import get_graph_client
                gc = await get_graph_client()
                # to_emails 에서 ip-lab 주소 찾기
                to_addrs = mail.to_emails or []
                mailbox = next(
                    (e["address"] for e in to_addrs if "ip-lab.co.kr" in e.get("address", "")),
                    None,
                ) or mail.from_email
                url = f"/users/{mailbox}/messages/{mail.graph_message_id}/attachments/{att.graph_attachment_id}/$value"
                resp = await gc.get(url)
                return Response(content=resp.content, media_type=att.content_type or "image/png")
            except Exception:
                pass

    raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")


# ── 헬퍼 ──────────────────────────────────────────────────────────
def _rewrite_cid(html: str, mail_id: str) -> str:
    """body_html 내 cid: 참조를 백엔드 프록시 URL로 교체"""
    return re.sub(
        r'src=["\']cid:([^"\'>\s]+)["\']',
        lambda m: f'src="/api/mails/{mail_id}/inline/{m.group(1)}"',
        html,
        flags=re.IGNORECASE,
    )
