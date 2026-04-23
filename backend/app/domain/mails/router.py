import base64
import re
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
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
        "case_info": _case_detail(case) if case else None,
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


# ── 사건 수동 연결 ────────────────────────────────────────────────
class LinkCaseBody(BaseModel):
    case_number: str | None = None  # None이면 연결 해제


@router.patch("/{mail_id}/case")
async def link_case(
    mail_id: uuid.UUID,
    body: LinkCaseBody,
    db: AsyncSession = Depends(get_db),
):
    """메일에 사건을 수동으로 연결하거나 해제"""
    mail_result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
    mail = mail_result.scalar_one_or_none()
    if not mail:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")

    if body.case_number:
        case_result = await db.execute(select(Case).where(Case.case_number == body.case_number))
        case = case_result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail=f"사건번호 '{body.case_number}'를 찾을 수 없습니다.")
        mail.case_id = case.id
        await db.commit()
        return {"status": "linked", "case_number": case.case_number, "case_info": _case_detail(case)}
    else:
        mail.case_id = None
        await db.commit()
        return {"status": "unlinked"}


# ── 수동 초안 생성 ───────────────────────────────────────────────
@router.post("/{mail_id}/draft")
async def create_manual_draft(mail_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """초안이 없을 때 빈 초안 생성 (직접 작성용)"""
    mail_result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
    mail = mail_result.scalar_one_or_none()
    if not mail:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")

    existing = await db.execute(
        select(DraftResponse).where(
            DraftResponse.source_mail_id == mail_id,
            DraftResponse.approval_status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 처리 중인 초안이 있습니다.")

    draft = DraftResponse(
        source_mail_id=mail_id,
        case_id=mail.case_id,
        generated_body_ko="",
        generated_body_en="",
        suggested_to=[],
        suggested_cc=[],
        approval_status="pending",
    )
    db.add(draft)
    await db.commit()
    return {"status": "created", "draft_id": str(draft.id)}


# ── 메일 번역 요청 ───────────────────────────────────────────────
@router.post("/{mail_id}/translate")
async def translate_mail(mail_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Claude로 본문 번역 후 ai_translation 필드 저장"""
    mail_result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
    mail = mail_result.scalar_one_or_none()
    if not mail:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
    if not mail.body_text:
        raise HTTPException(status_code=400, detail="번역할 본문이 없습니다.")

    try:
        import anthropic
        from app.config import get_settings
        settings = get_settings()
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": (
                    "다음 메일 본문을 한국어로 번역해주세요. 번역문만 출력하세요.\n\n"
                    + mail.body_text[:3000]
                ),
            }],
        )
        translation = response.content[0].text
        mail.ai_translation = translation
        await db.commit()
        return {"status": "ok", "translation": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"번역 실패: {e}")


# ── 인라인 이미지 프록시 ───────────────────────────────────────────
@router.get("/{mail_id}/inline/{content_id:path}")
async def get_inline_image(
    mail_id: uuid.UUID,
    content_id: str,
    db: AsyncSession = Depends(get_db),
):
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
        mail_result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
        mail = mail_result.scalar_one_or_none()
        if mail and mail.graph_message_id:
            try:
                from app.connectors.outlook.client import get_graph_client
                gc = get_graph_client()
                to_addrs = mail.to_emails or []
                mailbox = next(
                    (e["address"] for e in to_addrs if "ip-lab.co.kr" in e.get("address", "")),
                    None,
                ) or mail.from_email
                url = f"/users/{mailbox}/messages/{mail.graph_message_id}/attachments/{att.graph_attachment_id}/$value"
                resp = await gc.get(url)
                return Response(content=resp, media_type=att.content_type or "image/png")
            except Exception:
                pass

    raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")


# ── 헬퍼 ──────────────────────────────────────────────────────────
def _rewrite_cid(html: str, mail_id: str) -> str:
    return re.sub(
        r'src=["\']cid:([^"\'>\s]+)["\']',
        lambda m: f'src="/api/mails/{mail_id}/inline/{m.group(1)}"',
        html,
        flags=re.IGNORECASE,
    )


def _case_detail(case: Case) -> dict:
    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "your_ref": case.your_ref,
        "title_ko": case.title_ko,
        "title_en": case.title_en,
        "client_name": case.client_name,
        "applicant": case.applicant,
        "applicant_contact": case.applicant_contact,
        "country": case.country,
        "case_type": case.case_type,
        "attorney": case.attorney,
        "department": case.department,
        "status": case.status,
        "app_number": case.app_number,
        "reg_number": case.reg_number,
        "deadline": case.deadline.isoformat() if case.deadline else None,
        "filed_at": case.filed_at.isoformat() if case.filed_at else None,
        "registered_at": case.registered_at.isoformat() if case.registered_at else None,
        "priority_date": case.priority_date.isoformat() if case.priority_date else None,
        "public_notice_exception_date": case.public_notice_exception_date.isoformat() if case.public_notice_exception_date else None,
        "exam_request_date": case.exam_request_date.isoformat() if case.exam_request_date else None,
        "exam_request_deadline": case.exam_request_deadline.isoformat() if case.exam_request_deadline else None,
        "published_at": case.published_at.isoformat() if case.published_at else None,
        "intl_filed_at": case.intl_filed_at.isoformat() if case.intl_filed_at else None,
        "national_phase_at": case.national_phase_at.isoformat() if case.national_phase_at else None,
        "notes": case.notes,
        "ipc": case.ipc,
    }
