"""
관리 엔드포인트 - Webhook 등록, 수동 동기화 등
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.outlook.delta_sync import DeltaSyncService
from app.connectors.outlook.webhook import SubscriptionManager
from app.database import get_db

router = APIRouter()

OUTLOOK_USER_ID = "me"  # 실제 운영 시 특정 사용자 ID로 변경


@router.post("/webhook/register")
async def register_webhook():
    """Graph Webhook Subscription 등록/갱신"""
    try:
        manager = SubscriptionManager(OUTLOOK_USER_ID)
        result = await manager.create_or_renew()
        return {"status": "ok", "subscription_id": result.get("id"), "expiry": result.get("expirationDateTime")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def manual_sync(background_tasks: BackgroundTasks):
    """수동 Delta Query 동기화 트리거"""
    background_tasks.add_task(_run_sync)
    return {"status": "sync_started"}


async def _run_sync():
    from app.workflow.inbound import process_incoming_mail
    sync = DeltaSyncService(OUTLOOK_USER_ID)
    messages = await sync.sync()
    for msg in messages:
        process_incoming_mail.delay(user_id=OUTLOOK_USER_ID, message_id=msg["id"])
