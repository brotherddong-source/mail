"""
Microsoft OAuth 로그인
1. /auth/login         → Microsoft 로그인 페이지로 리다이렉트
2. /auth/callback      → 토큰 교환 + JWT 발급
3. /auth/me            → 현재 사용자 정보
4. /auth/logout        → 로그아웃
"""
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.domain.users.models import User

router = APIRouter()
settings = get_settings()

MS_AUTH_URL = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/authorize"
MS_TOKEN_URL = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/token"
SCOPES = "openid email profile Mail.Read Mail.ReadWrite Mail.Send offline_access"
REDIRECT_URI = "https://mail-production-3eba.up.railway.app/auth/callback"

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7일


# ----------------------------------------------------------------
# JWT 유틸 (라우트보다 먼저 정의 — Depends() 기본값 평가 시점 때문)
# ----------------------------------------------------------------
def _create_jwt(user_id: str, email: str, is_admin: bool) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    payload = _decode_jwt(auth[7:])
    result = await db.execute(select(User).where(User.email == payload["email"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="접근 권한이 없습니다.")
    return user


# ----------------------------------------------------------------
# 로그인 → Microsoft로 리다이렉트
# ----------------------------------------------------------------
@router.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": settings.azure_client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "prompt": "select_account",
    }
    return RedirectResponse(f"{MS_AUTH_URL}?{urlencode(params)}")


# ----------------------------------------------------------------
# Microsoft 콜백 → JWT 발급
# ----------------------------------------------------------------
@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 토큰 교환
    async with httpx.AsyncClient() as client:
        resp = await client.post(MS_TOKEN_URL, data={
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if not resp.is_success:
            raise HTTPException(status_code=400, detail="Microsoft 토큰 교환 실패")
        token_data = resp.json()

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    # Microsoft Graph에서 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        me_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        me = me_resp.json()

    ms_email = (me.get("mail") or me.get("userPrincipalName") or "").lower()
    ms_user_id = me.get("id")

    # 허용된 직원인지 확인
    result = await db.execute(select(User).where(User.email == ms_email))
    user = result.scalar_one_or_none()

    if not user:
        # ip-lab.co.kr 도메인이면 자동 등록 (미등록 직원 대비)
        if ms_email.endswith("@ip-lab.co.kr"):
            user = User(
                name=me.get("displayName", ms_email.split("@")[0]),
                email=ms_email,
                is_active=True,
            )
            db.add(user)
        else:
            frontend = "https://mail-ruby-rho.vercel.app"
            return RedirectResponse(f"{frontend}/?error=unauthorized")

    if not user.is_active:
        frontend = "https://mail-ruby-rho.vercel.app"
        return RedirectResponse(f"{frontend}/?error=inactive")

    # 토큰 저장 (개인 메일 연동)
    user.ms_access_token = access_token
    user.ms_refresh_token = refresh_token
    user.ms_user_id = ms_user_id
    user.ms_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    user.personal_mailbox_connected = True
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    # 개인 Webhook 등록 (백그라운드, 실패해도 로그인 계속)
    from app.connectors.outlook.webhook import SubscriptionManager
    try:
        manager = SubscriptionManager(ms_user_id, access_token=access_token)
        await manager.create_or_renew()
        user.personal_mailbox_connected = True
        await db.commit()
    except Exception:
        pass

    # JWT 발급 후 프론트엔드로 리다이렉트
    jwt_token = _create_jwt(str(user.id), user.email, user.is_admin)
    frontend = "https://mail-ruby-rho.vercel.app"
    return RedirectResponse(f"{frontend}/auth?token={jwt_token}")


# ----------------------------------------------------------------
# 현재 사용자 정보
# ----------------------------------------------------------------
@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "is_admin": user.is_admin,
        "personal_mailbox_connected": user.personal_mailbox_connected,
    }
