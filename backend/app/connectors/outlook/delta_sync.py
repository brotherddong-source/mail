"""
메일 증분 동기화 — Redis 없이 직접 Graph API 조회
중복은 inbound._async_process에서 graph_message_id 기준으로 처리
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.connectors.outlook.client import get_graph_client

logger = logging.getLogger(__name__)


class DeltaSyncService:
    def __init__(self, user_id: str, days_back: int = 30):
        self.user_id = user_id
        self.days_back = days_back
        self.client = get_graph_client()

    async def sync(self) -> list[dict]:
        """
        최근 N일 메일 조회.
        중복 방지는 inbound._async_process의 graph_message_id 체크에서 처리.
        """
        since = (
            datetime.now(timezone.utc) - timedelta(days=self.days_back)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        token = await self.client._get_token()
        url = (
            f"https://graph.microsoft.com/v1.0/users/{self.user_id}/messages"
            f"?$select=id,subject,from,toRecipients,ccRecipients,receivedDateTime,"
            "hasAttachments,conversationId,internetMessageId,bodyPreview"
            f"&$filter=receivedDateTime ge {since}"
            "&$top=50"
            "&$orderby=receivedDateTime desc"
        )

        messages: list[dict] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            data = resp.json()
            messages = data.get("value", [])

        logger.info("메일 조회: %d건 (user: %s, 최근 %d일)", len(messages), self.user_id, self.days_back)
        return messages
