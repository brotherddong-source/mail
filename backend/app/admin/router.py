"""
관리 엔드포인트 - Webhook 등록, 수동 동기화 등
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.outlook.webhook import SubscriptionManager
from app.database import get_db

router = APIRouter()

# 공용 메일함 목록 (Application 권한으로 접근)
SHARED_MAILBOXES = [
    "ip@ip-lab.co.kr",
    "mail@ip-lab.co.kr",
]


@router.post("/webhook/register")
async def register_webhook():
    """공용 메일함 Graph Webhook Subscription 등록/갱신"""
    results = []
    errors = []
    for mailbox in SHARED_MAILBOXES:
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
    return {"status": "sync_started", "mailboxes": SHARED_MAILBOXES}


async def _run_sync():
    import asyncio
    from app.connectors.outlook.delta_sync import DeltaSyncService
    from app.workflow.inbound import _async_process
    for mailbox in SHARED_MAILBOXES:
        try:
            sync = DeltaSyncService(mailbox)
            messages = await sync.sync()
            for msg in messages:
                asyncio.create_task(_async_process(user_id=mailbox, message_id=msg["id"]))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("sync 실패 (%s): %s", mailbox, e)
