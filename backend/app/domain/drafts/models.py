import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DraftResponse(Base):
    __tablename__ = "draft_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_mail_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mail_messages.id", ondelete="SET NULL")
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL")
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    generated_body_ko: Mapped[str | None] = mapped_column(Text)
    generated_body_en: Mapped[str | None] = mapped_column(Text)
    reviewer_body: Mapped[str | None] = mapped_column(Text)  # 검토자가 수정한 본문
    suggested_to: Mapped[dict | None] = mapped_column(JSONB)
    suggested_cc: Mapped[dict | None] = mapped_column(JSONB)
    approval_status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )  # pending/approved/rejected
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    graph_sent_message_id: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source_mail: Mapped["MailMessage"] = relationship(  # noqa: F821
        "MailMessage", back_populates="draft_responses"
    )
    case: Mapped["Case"] = relationship("Case", back_populates="draft_responses")  # noqa: F821


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str | None] = mapped_column(String(100))
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
