from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화
    yield
    # 종료 시 정리


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


# 라우터 등록 (각 Step에서 추가됨)
# from app.auth.router import router as auth_router
# from app.connectors.outlook.webhook import router as webhook_router
# from app.domain.mails.router import router as mail_router
# from app.domain.cases.router import router as case_router
# from app.domain.drafts.router import router as draft_router
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])
# app.include_router(mail_router, prefix="/api/mails", tags=["mails"])
# app.include_router(case_router, prefix="/api/cases", tags=["cases"])
# app.include_router(draft_router, prefix="/api/drafts", tags=["drafts"])
