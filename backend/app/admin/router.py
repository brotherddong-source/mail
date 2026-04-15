"""
관리 엔드포인트 - Webhook 등록, 수동 동기화 등
"""
import logging

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select

from app.config import get_settings
from app.connectors.outlook.webhook import SubscriptionManager
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _get_mailboxes() -> list[str]:
    return settings.sync_mailbox_list


@router.post("/webhook/register")
async def register_webhook():
    """공용 메일함 Graph Webhook Subscription 등록/갱신"""
    results = []
    errors = []
    for mailbox in _get_mailboxes():
        try:
            manager = SubscriptionManager(mailbox)
            result = await manager.create_or_renew()
            results.append({
                "mailbox": mailbox,
                "subscription_id": result.get("id"),
                "expiry": result.get("expirationDateTime"),
            })
        except Exception as e:
            errors.append({"mailbox": mailbox, "error": str(e)})

    return {
        "status": "ok" if not errors else "partial",
        "registered": results,
        "errors": errors,
    }


@router.post("/sync")
async def manual_sync(background_tasks: BackgroundTasks):
    """수동 Delta Query 동기화 트리거 (공용 메일함)"""
    background_tasks.add_task(_run_sync)
    return {"status": "sync_started", "mailboxes": _get_mailboxes()}


async def _run_sync():
    import asyncio
    from app.connectors.outlook.delta_sync import DeltaSyncService
    from app.workflow.inbound import _async_process
    for mailbox in _get_mailboxes():
        try:
            sync = DeltaSyncService(mailbox)
            messages = await sync.sync()
            for msg in messages:
                asyncio.create_task(_async_process(user_id=mailbox, message_id=msg["id"]))
        except Exception as e:
            logger.error("sync 실패 (%s): %s", mailbox, e)


@router.post("/reanalyze")
async def reanalyze_errors(background_tasks: BackgroundTasks):
    """처리 실패(error) 또는 미분석(pending) 메일 재분석 트리거"""
    background_tasks.add_task(_run_reanalyze)
    return {"status": "reanalyze_started"}


async def _run_reanalyze():
    """error/pending 상태 메일을 AI 재분석"""
    import asyncio
    from app.domain.mails.models import MailMessage
    from app.workflow.inbound import _analyze_and_draft

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MailMessage.id, MailMessage.graph_message_id)
            .where(MailMessage.processing_status.in_(["error", "pending"]))
            .limit(50)
        )
        rows = result.all()

    logger.info("재분석 대상: %d건", len(rows))
    for mail_id, graph_message_id in rows:
        try:
            await _analyze_and_draft(mail_id, graph_message_id)
        except Exception as e:
            logger.error("재분석 실패 (mail_id=%s): %s", mail_id, e)
