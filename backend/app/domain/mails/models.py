import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MailMessage(Base):
    __tablename__ = "mail_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_message_id: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    internet_message_id: Mapped[str | None] = mapped_column(String(500))
    conversation_id: Mapped[str | None] = mapped_column(String(500))
    from_email: Mapped[str | None] = mapped_column(String(200))
    from_name: Mapped[str | None] = mapped_column(String(200))
    to_emails: Mapped[dict | None] = mapped_column(JSONB)
    cc_emails: Mapped[dict | None] = mapped_column(JSONB)
    subject: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_language: Mapped[str | None] = mapped_column(String(10))
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL")
    )
    requires_reply: Mapped[bool | None] = mapped_column(Boolean)
    priority: Mapped[str | None] = mapped_column(String(10))  # low/medium/high
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_translation: Mapped[str | None] = mapped_column(Text)
    ai_classification: Mapped[str | None] = mapped_column(String(50))
    processing_status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="mail_messages")  # noqa: F821
    attachments: Mapped[list["MailAttachment"]] = relationship(
        "MailAttachment", back_populates="mail"
    )
    draft_responses: Mapped[list["DraftResponse"]] = relationship(  # noqa: F821
        "DraftResponse", back_populates="source_mail"
    )


class MailAttachment(Base):
    __tablename__ = "mail_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mail_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mail_messages.id", ondelete="CASCADE")
    )
    graph_attachment_id: Mapped[str | None] = mapped_column(String(500))
    filename: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    stored_path: Mapped[str | None] = mapped_column(Text)

    # Relationships
    mail: Mapped["MailMessage"] = relationship("MailMessage", back_populates="attachments")
