"""
수신 메일 처리 파이프라인
흐름: Graph 메일 수신 → DB 저장 → 사건 매칭 → AI 분석 → 초안 생성
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.connectors.outlook.client import get_graph_client
from app.database import AsyncSessionLocal
from app.domain.cases.matcher import CaseMatcher
from app.domain.drafts.models import DraftResponse
from app.domain.mails.models import MailAttachment, MailMessage

logger = logging.getLogger(__name__)


async def _async_process(user_id: str, message_id: str) -> None:
    """실제 비동기 처리 로직 — 저장과 AI 분석을 분리해 에러 시에도 메일은 보존"""
    graph = get_graph_client()

    # ── 1단계: 메일 저장 (별도 트랜잭션 — 항상 commit) ──────────────────
    async with AsyncSessionLocal() as db:
        # 중복 체크
        existing = await db.execute(
            select(MailMessage).where(MailMessage.graph_message_id == message_id)
        )
        if existing.scalar_one_or_none():
            logger.info("이미 처리된 메일 (message_id=%s)", message_id)
            return

        # Graph API에서 메일 상세 조회
        try:
            raw = await graph.get_message(user_id, message_id)
        except Exception as e:
            logger.error("Graph 메일 조회 실패 (message_id=%s): %s", message_id, e)
            return

        attachments_raw = []
        if raw.get("hasAttachments"):
            try:
                attachments_raw = await graph.get_message_attachments(user_id, message_id)
            except Exception as e:
                logger.warning("첨부파일 조회 실패 (message_id=%s): %s", message_id, e)

        mail = _map_to_mail_message(raw)
        db.add(mail)
        await db.flush()

        for att in attachments_raw:
            db.add(MailAttachment(
                mail_id=mail.id,
                graph_attachment_id=att.get("id"),
                filename=att.get("name"),
                content_type=att.get("contentType"),
                size_bytes=att.get("size"),
            ))

        await db.commit()
        mail_id = mail.id
        logger.info("메일 저장 완료 (id=%s, subject=%s)", mail_id, mail.subject)

    # ── 2단계: 사건 매칭 + AI 분석 (실패해도 메일은 이미 저장됨) ──────────
    try:
        await _analyze_and_draft(mail_id, message_id)
    except Exception as e:
        logger.error("AI 분석 실패 (mail_id=%s): %s", mail_id, e)
        # 실패 시 status를 'error'로 업데이트
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
                mail = result.scalar_one_or_none()
                if mail:
                    mail.processing_status = "error"
                    await db.commit()
        except Exception:
            pass


async def _analyze_and_draft(mail_id: uuid.UUID, message_id: str) -> None:
    """AI 분석 및 초안 생성 — 별도 트랜잭션"""
    from app.ai.analyzer import MailAnalyzer
    from app.ai.drafter import MailDrafter

    analyzer = MailAnalyzer()
    drafter = MailDrafter()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MailMessage).where(MailMessage.id == mail_id))
        mail = result.scalar_one_or_none()
        if not mail:
            return

        # 사건 매칭
        from app.domain.cases.matcher import CaseMatcher
        matcher = CaseMatcher(db)
        match_result = await matcher.match(
            subject=mail.subject or "",
            body_text=mail.body_text or "",
            from_email=mail.from_email or "",
            conversation_id=mail.conversation_id,
        )

        if match_result.matched_case:
            mail.case_id = match_result.matched_case.id
            case_dict = {
                "case_number": match_result.matched_case.case_number,
                "client_name": match_result.matched_case.client_name,
                "country": match_result.matched_case.country,
                "case_type": match_result.matched_case.case_type,
                "status": match_result.matched_case.status,
                "deadline": str(match_result.matched_case.deadline) if match_result.matched_case.deadline else None,
            }
        else:
            case_dict = None

        # AI 분석
        mail_dict = {
            "from_email": mail.from_email,
            "from_name": mail.from_name,
            "subject": mail.subject,
            "body_text": mail.body_text,
            "received_at": str(mail.received_at),
        }
        analysis = await analyzer.analyze(mail_dict, case_dict, mask_sensitive=True)

        mail.ai_summary = analysis.summary_ko
        mail.ai_translation = analysis.translation_ko
        mail.ai_classification = analysis.classification.value
        mail.requires_reply = analysis.requires_reply
        mail.priority = analysis.urgency.value
        mail.processing_status = "analyzed"

        # 회신 필요 시 초안 생성
        if analysis.requires_reply:
            history_result = await db.execute(
                select(MailMessage)
                .where(
                    MailMessage.case_id == mail.case_id,
                    MailMessage.id != mail.id,
                )
                .order_by(MailMessage.received_at.desc())
                .limit(5)
            )
            history_mails = history_result.scalars().all()
            history_dicts = [
                {
                    "from_email": m.from_email,
                    "received_at": str(m.received_at),
                    "subject": m.subject,
                    "ai_summary": m.ai_summary,
                }
                for m in history_mails
            ]

            draft_result = await drafter.draft(
                mail_data=mail_dict,
                analysis=analysis.model_dump(),
                case_info=case_dict,
                mail_history=history_dicts,
            )

            draft = DraftResponse(
                source_mail_id=mail.id,
                case_id=mail.case_id,
                generated_body_ko=draft_result.draft_ko,
                generated_body_en=draft_result.draft_en,
                suggested_to=[r.model_dump() for r in draft_result.suggested_recipients if r.role == "to"],
                suggested_cc=[r.model_dump() for r in draft_result.suggested_recipients if r.role == "cc"],
                approval_status="pending",
            )
            db.add(draft)
            mail.processing_status = "draft_ready"

        await db.commit()
        logger.info("AI 분석 완료 (id=%s, status=%s)", mail.id, mail.processing_status)


def _map_to_mail_message(raw: dict) -> MailMessage:
    """Graph API 응답 → MailMessage 모델 변환"""
    from_obj = raw.get("from", {}).get("emailAddress", {})
    received_raw = raw.get("receivedDateTime")
    received_at = datetime.fromisoformat(received_raw.replace("Z", "+00:00")) if received_raw else None

    body = raw.get("body", {})
    body_html = body.get("content", "") if body.get("contentType") == "html" else ""
    body_text = _strip_html(body.get("content", ""))

    return MailMessage(
        graph_message_id=raw["id"],
        internet_message_id=raw.get("internetMessageId"),
        conversation_id=raw.get("conversationId"),
        from_email=from_obj.get("address", "").lower(),
        from_name=from_obj.get("name", ""),
        to_emails=[
            r.get("emailAddress", {}) for r in raw.get("toRecipients", [])
        ],
        cc_emails=[
            r.get("emailAddress", {}) for r in raw.get("ccRecipients", [])
        ],
        subject=raw.get("subject"),
        body_text=body_text,
        body_html=body_html,
        received_at=received_at,
        has_attachments=raw.get("hasAttachments", False),
        processing_status="pending",
    )


def _strip_html(html: str) -> str:
    """간단한 HTML 태그 제거"""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
