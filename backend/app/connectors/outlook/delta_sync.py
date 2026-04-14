"""
Delta Query 기반 증분 메일 동기화
마지막 동기화 이후 변경된 메일만 가져옴
"""
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.connectors.outlook.client import get_graph_client

logger = logging.getLogger(__name__)
settings = get_settings()

DELTA_LINK_KEY = "outlook:delta_link:{user_id}"


class DeltaSyncService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = get_graph_client()

    async def _get_redis(self) -> aioredis.Redis:
        return aioredis.from_url(settings.redis_url, decode_responses=True)

    async def _get_delta_link(self) -> str | None:
        redis = await self._get_redis()
        key = DELTA_LINK_KEY.format(user_id=self.user_id)
        return await redis.get(key)

    async def _save_delta_link(self, delta_link: str) -> None:
        redis = await self._get_redis()
        key = DELTA_LINK_KEY.format(user_id=self.user_id)
        await redis.set(key, delta_link, ex=86400 * 7)  # 7일 유지

    async def sync(self) -> list[dict]:
        """
        Delta Query로 증분 동기화.
        Returns: 새로 수신/변경된 메일 목록
        """
        delta_link = await self._get_delta_link()
        messages: list[dict] = []

        if delta_link:
            # 이전 delta link로 변경분만 조회
            result = await self.client.get("", params={})
            # delta link는 전체 URL이므로 직접 요청
            result = await self._fetch_delta_url(delta_link)
        else:
            # 최초 동기화: 최근 7일치
            result = await self._initial_sync()

        messages.extend(result.get("value", []))

        # 다음 delta link 저장
        next_delta = result.get("@odata.deltaLink")
        if next_delta:
            await self._save_delta_link(next_delta)

        logger.info("Delta 동기화: %d건 수신 (user: %s)", len(messages), self.user_id)
        return messages

    async def _initial_sync(self) -> dict:
        """최초 delta 동기화 (초기화)"""
        import httpx
        token = await self.client._get_token()
        url = (
            f"https://graph.microsoft.com/v1.0/users/{self.user_id}/messages/delta"
            "?$select=id,subject,from,toRecipients,ccRecipients,receivedDateTime,"
            "hasAttachments,conversationId,internetMessageId,bodyPreview"
            "&$filter=receivedDateTime ge 2024-01-01T00:00:00Z"
            "&$top=50"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            return resp.json()

    async def _fetch_delta_url(self, delta_url: str) -> dict:
        """저장된 deltaLink URL로 직접 요청"""
        import httpx
        token = await self.client._get_token()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(delta_url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            return resp.json()
