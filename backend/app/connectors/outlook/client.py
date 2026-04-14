"""
Microsoft Graph API 클라이언트
MSAL을 통한 OAuth2 토큰 관리 및 Graph API 기본 요청 처리
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import msal

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


class GraphClient:
    """Microsoft Graph API 클라이언트 (Application Permission 기반)"""

    def __init__(self):
        self._msal_app = msal.ConfidentialClientApplication(
            client_id=settings.azure_client_id,
            client_credential=settings.azure_client_secret,
            authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
        )
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    async def _get_token(self) -> str:
        """토큰 획득 (캐시 우선, 만료 시 갱신)"""
        now = datetime.now(timezone.utc)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token

        result = self._msal_app.acquire_token_silent(GRAPH_SCOPES, account=None)
        if not result:
            result = self._msal_app.acquire_token_for_client(scopes=GRAPH_SCOPES)

        if "error" in result:
            raise RuntimeError(
                f"토큰 획득 실패: {result.get('error_description', result.get('error'))}"
            )

        self._token = result["access_token"]
        expires_in = result.get("expires_in", 3600)
        self._token_expires_at = now + timedelta(seconds=expires_in - 60)
        return self._token

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        """Graph API 요청 공통 처리"""
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            **kwargs.pop("headers", {}),
        }
        url = f"{GRAPH_BASE_URL}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)

        if response.status_code == 204:
            return None

        if not response.is_success:
            logger.error("Graph API 오류: %s %s → %s", method, url, response.text)
            response.raise_for_status()

        return response.json()

    async def get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self._request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Any:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        return await self._request("DELETE", path, **kwargs)

    # ----------------------------------------------------------------
    # 메일 조회
    # ----------------------------------------------------------------
    async def get_messages(
        self,
        user_id: str,
        top: int = 50,
        select: str = "id,subject,from,toRecipients,ccRecipients,receivedDateTime,hasAttachments,conversationId,internetMessageId,bodyPreview",
        filter_str: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {
            "$top": top,
            "$select": select,
            "$orderby": "receivedDateTime desc",
        }
        if filter_str:
            params["$filter"] = filter_str

        path = f"/users/{user_id}/messages"
        result = await self.get(path, params=params)
        return result.get("value", [])

    async def get_message(self, user_id: str, message_id: str) -> dict:
        """메일 상세 조회 (body 포함)"""
        select = "id,subject,from,toRecipients,ccRecipients,receivedDateTime,hasAttachments,conversationId,internetMessageId,body"
        return await self.get(
            f"/users/{user_id}/messages/{message_id}",
            params={"$select": select},
        )

    async def get_message_attachments(self, user_id: str, message_id: str) -> list[dict]:
        """첨부파일 메타데이터 목록 조회"""
        result = await self.get(
            f"/users/{user_id}/messages/{message_id}/attachments",
            params={"$select": "id,name,contentType,size"},
        )
        return result.get("value", [])

    # ----------------------------------------------------------------
    # 메일 발송
    # ----------------------------------------------------------------
    async def send_mail(
        self,
        user_id: str,
        subject: str,
        body_html: str,
        to_recipients: list[dict],
        cc_recipients: list[dict] | None = None,
        reply_to_message_id: str | None = None,
    ) -> None:
        """메일 발송 (수동 승인 후에만 호출)"""
        message = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": [
                {"emailAddress": {"address": r["email"], "name": r.get("name", "")}}
                for r in to_recipients
            ],
        }
        if cc_recipients:
            message["ccRecipients"] = [
                {"emailAddress": {"address": r["email"], "name": r.get("name", "")}}
                for r in cc_recipients
            ]

        if reply_to_message_id:
            # 회신으로 발송
            await self.post(
                f"/users/{user_id}/messages/{reply_to_message_id}/reply",
                json={"message": message},
            )
        else:
            await self.post(
                f"/users/{user_id}/sendMail",
                json={"message": message, "saveToSentItems": True},
            )
        logger.info("메일 발송 완료: %s → %s", subject, [r["email"] for r in to_recipients])


# 싱글턴 인스턴스 (애플리케이션 레벨)
_graph_client: GraphClient | None = None


def get_graph_client() -> GraphClient:
    global _graph_client
    if _graph_client is None:
        _graph_client = GraphClient()
    return _graph_client
