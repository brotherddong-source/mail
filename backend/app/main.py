import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()


async def _background_seed() -> None:
    """uvicorn이 healthcheck에 응답할 수 있도록 백그라운드에서 시드 실행"""
    try:
        async with AsyncSessionLocal() as db:
            from app.domain.users.seed import seed_users
            await seed_users(db)
        logger.info("직원 시드 완료")
    except Exception as e:
        logger.error("직원 시드 실패 (무시하고 계속): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    # 백그라운드로 시드 예약 — lifespan이 즉시 yield해서 healthcheck가 바로 통과
    asyncio.create_task(_background_seed())
    yield


app = FastAPI(
    title="특허사무소 메일 자동화 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}


# 라우터 등록 — 임포트 실패 시 /health 만 남는 문제를 방지하기 위해 개별 try/except
_ROUTERS_OK = True

try:
    from app.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    logger.info("auth router 등록 완료")
except Exception:
    logger.error("auth router 로드 실패:\n%s", traceback.format_exc())
    _ROUTERS_OK = False

try:
    from app.connectors.outlook.webhook import router as webhook_router
    app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])
    logger.info("webhook router 등록 완료")
except Exception:
    logger.error("webhook router 로드 실패:\n%s", traceback.format_exc())

try:
    from app.domain.mails.router import router as mail_router
    app.include_router(mail_router, prefix="/api/mails", tags=["mails"])
    logger.info("mails router 등록 완료")
except Exception:
    logger.error("mails router 로드 실패:\n%s", traceback.format_exc())

try:
    from app.domain.drafts.router import router as draft_router
    app.include_router(draft_router, prefix="/api/drafts", tags=["drafts"])
    logger.info("drafts router 등록 완료")
except Exception:
    logger.error("drafts router 로드 실패:\n%s", traceback.format_exc())

try:
    from app.domain.cases.router import router as case_router
    app.include_router(case_router, prefix="/api/cases", tags=["cases"])
    logger.info("cases router 등록 완료")
except Exception:
    logger.error("cases router 로드 실패:\n%s", traceback.format_exc())

try:
    from app.admin.router import router as admin_router
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    logger.info("admin router 등록 완료")
except Exception:
    logger.error("admin router 로드 실패:\n%s", traceback.format_exc())


@app.get("/debug/routes")
async def list_routes():
    """등록된 라우트 목록 확인용 (임시)"""
    return [{"path": r.path, "methods": list(r.methods)} for r in app.routes]
