"""
Microsoft Graph Webhook (Change Notification) 처리
- Subscription 등록/갱신
- Webhook 수신 엔드포인트
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from app.config import get_settings
from app.connectors.outlook.client import get_graph_client

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

SUBSCRIPTION_RESOURCE = "me/messages"
SUBSCRIPTION_CHANGE_TYPES = "created,updated"
SUBSCRIPTION_EXPIRY_HOURS = 48  # Graph API 최대 4230분 (약 70시간)


class SubscriptionManager:
    def __init__(self, user_id: str, access_token: str | None = None):
        self.user_id = user_id
        # 개인 토큰이 있으면 직접 사용, 없으면 Application 권한 클라이언트 사용
        self._access_token = access_token
        self.client = get_graph_client()

    async def create_or_renew(self) -> dict:
        """Subscription 생성 또는 갱신"""
        expiry = (
            datetime.now(timezone.utc) + timedelta(hours=SUBSCRIPTION_EXPIRY_HOURS)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "changeType": SUBSCRIPTION_CHANGE_TYPES,
            "notificationUrl": settings.graph_webhook_notification_url,
            "resource": f"/users/{self.user_id}/messages",
            "expirationDateTime": expiry,
            "clientState": settings.secret_key[:32],  # 검증용 secret
        }

        existing = await self._get_existing_subscription()
        if existing:
            # 갱신
            result = await self.client.patch(
                f"/subscriptions/{existing['id']}",
                json={"expirationDateTime": expiry},
            )
            logger.info("Subscription 갱신: %s (만료: %s)", existing["id"], expiry)
            return result
        else:
            # 신규 등록
            result = await self.client.post("/subscriptions", json=payload)
            logger.info("Subscription 생성: %s (만료: %s)", result.get("id"), expiry)
            return result

    async def _get_existing_subscription(self) -> dict | None:
        """기존 유효한 subscription 조회"""
        result = await self.client.get("/subscriptions")
        subscriptions = result.get("value", [])
        notification_url = settings.graph_webhook_notification_url
        for sub in subscriptions:
            if sub.get("notificationUrl") == notification_url:
                return sub
        return None

    async def delete_all(self) -> None:
        """모든 subscription 삭제 (개발/테스트용)"""
        result = await self.client.get("/subscriptions")
        for sub in result.get("value", []):
            await self.client.delete(f"/subscriptions/{sub['id']}")
            logger.info("Subscription 삭제: %s", sub["id"])


# ----------------------------------------------------------------
# FastAPI Webhook 엔드포인트
# ----------------------------------------------------------------

@router.post("/outlook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    validationToken: str | None = Query(default=None),
):
    """
    Graph Webhook 수신 엔드포인트.
    - 최초 등록 시 validationToken echo 응답
    - 이후 알림 수신 → 백그라운드로 처리
    """
    # Subscription 검증 단계
    if validationToken:
        return Response(content=validationToken, media_type="text/plain", status_code=200)

    body = await request.json()

    # clientState 검증
    for notification in body.get("value", []):
        client_state = notification.get("clientState", "")
        if client_state != settings.secret_key[:32]:
            logger.warning("Webhook clientState 불일치 — 무시")
            raise HTTPException(status_code=401, detail="Invalid clientState")

        background_tasks.add_task(_process_notification, notification)

    return Response(status_code=202)


async def _process_notification(notification: dict) -> None:
    """수신된 알림을 처리 (수신 파이프라인 트리거)"""
    resource = notification.get("resource", "")
    change_type = notification.get("changeType", "")
    logger.info("Webhook 알림 수신: %s (%s)", resource, change_type)

    # 메일 ID 추출: Users/{userId}/Messages/{messageId}
    parts = resource.split("/")
    if len(parts) >= 4 and parts[2].lower() == "messages":
        message_id = parts[3]
        user_id = parts[1]
        # Celery 없이 asyncio task로 직접 실행 (Redis 불필요)
        import asyncio
        from app.workflow.inbound import _async_process
        asyncio.create_task(_async_process(user_id=user_id, message_id=message_id))
