import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.templates.mail_templates import OUTBOUND_TEMPLATES, INBOUND_TYPES, get_template_for_mail
from app.templates.signatures import get_signatures_for_user
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


# ── 템플릿 목록 ────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates(
    mail_id: str | None = Query(default=None, description="추천 우선순위를 위한 메일 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    사용 가능한 발신 템플릿 목록 + 메일 ID가 주어지면 추천 템플릿 표시
    """
    recommended_id: str | None = None

    if mail_id:
        from app.domain.mails.models import MailMessage
        result = await db.execute(
            select(MailMessage).where(MailMessage.id == mail_id)
        )
        mail = result.scalar_one_or_none()
        if mail:
            matched = get_template_for_mail(
                subject=mail.subject or "",
                body=mail.body_text or "",
                direction="inbound",
            )
            if matched:
                recommended_id = matched.get("reply_template_id")

    templates = []
    for _body, meta in OUTBOUND_TEMPLATES:
        templates.append({
            "id": meta["id"],
            "name": meta["name"],
            "category": meta["category"],
            "language": meta["language"],
            "use_case": meta.get("use_case", ""),
            "subject_pattern": meta.get("subject_pattern", ""),
            "variables": meta.get("variables", []),
            "is_recommended": meta["id"] == recommended_id,
        })

    # 추천 항목 맨 앞으로
    templates.sort(key=lambda t: (0 if t["is_recommended"] else 1, t["category"]))
    return {"templates": templates, "recommended_id": recommended_id}


# ── 서명 목록 ────────────────────────────────────────────────────

@router.get("/signatures")
async def list_signatures(
    sender_email: str = Query(..., description="발신자 이메일"),
):
    """발신자 이메일 기준 사용 가능한 서명 목록"""
    sigs = get_signatures_for_user(sender_email)
    return {"signatures": sigs}


# ── 재생성 ────────────────────────────────────────────────────────

class RegenerateRequest(BaseModel):
    template_id: str | None = None
    signature_id: str | None = None
    sender_email: str | None = None  # 서명 선택 시 발신자 지정


@router.post("/{draft_id}/regenerate")
async def regenerate_draft(
    draft_id: uuid.UUID,
    body: RegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    선택한 템플릿·서명으로 초안 재생성.
    template_id: OUTBOUND_TEMPLATES의 id
    signature_id: signatures.get_signatures_for_user()의 id
    """
    from app.domain.drafts.models import DraftResponse
    from app.domain.mails.models import MailMessage
    from app.ai.drafter import MailDrafter
    from app.templates.signatures import get_signatures_for_user as _sigs

    result = await db.execute(select(DraftResponse).where(DraftResponse.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="초안을 찾을 수 없습니다.")

    mail_result = await db.execute(
        select(MailMessage).where(MailMessage.id == draft.source_mail_id)
    )
    mail = mail_result.scalar_one_or_none()
    if not mail:
        raise HTTPException(status_code=404, detail="원본 메일을 찾을 수 없습니다.")

    # 선택한 서명 가져오기
    signature_body_en: str | None = None
    signature_body_ko: str | None = None
    if body.sender_email and body.signature_id:
        sigs = _sigs(body.sender_email)
        for sig in sigs:
            if sig["id"] == body.signature_id:
                if sig["language"] == "en":
                    signature_body_en = sig["body"]
                else:
                    signature_body_ko = sig["body"]

    # 선택한 템플릿 힌트
    template_hint = ""
    if body.template_id:
        from app.templates.mail_templates import OUTBOUND_BY_ID
        tpl = OUTBOUND_BY_ID.get(body.template_id)
        if tpl:
            tpl_body, tpl_meta = tpl
            template_hint = (
                f"\n[선택된 템플릿: {tpl_meta['name']}]\n"
                f"용도: {tpl_meta.get('use_case', '')}\n"
                f"참고 형식:\n{tpl_body[:600]}\n"
            )

    # Claude 재생성
    mail_dict = {
        "from_email": mail.from_email,
        "from_name": mail.from_name,
        "subject": mail.subject,
        "body_text": mail.body_text,
    }
    analysis_dict = {
        "classification": mail.ai_classification or "requires_reply",
        "urgency": mail.priority or "medium",
        "key_points": [],
        "deadline_detected": None,
        "review_warnings": [],
        "template_hint": template_hint,
    }

    try:
        drafter = MailDrafter()
        new_draft_result = await drafter.draft(
            mail_data=mail_dict,
            analysis=analysis_dict,
        )

        # 서명 붙이기
        ko = new_draft_result.draft_ko
        en = new_draft_result.draft_en
        if signature_body_ko:
            ko = ko.rstrip() + "\n" + signature_body_ko
        if signature_body_en:
            en = en.rstrip() + "\n" + signature_body_en

        draft.generated_body_ko = ko
        draft.generated_body_en = en
        draft.approval_status = "pending"
        await db.commit()

        return {
            "status": "regenerated",
            "draft_ko": ko,
            "draft_en": en,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재생성 실패: {e}")
