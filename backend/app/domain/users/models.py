import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Microsoft OAuth 토큰 (개인 메일 연동용)
    ms_access_token: Mapped[str | None] = mapped_column(Text)
    ms_refresh_token: Mapped[str | None] = mapped_column(Text)
    ms_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ms_user_id: Mapped[str | None] = mapped_column(String(200))  # Azure Object ID

    # 메일함 연결 상태
    personal_mailbox_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    personal_webhook_id: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
