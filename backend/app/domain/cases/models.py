import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    app_number: Mapped[str | None] = mapped_column(String(50))
    reg_number: Mapped[str | None] = mapped_column(String(50))
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_domain: Mapped[str | None] = mapped_column(String(100))  # 이메일 도메인 매칭용
    country: Mapped[str] = mapped_column(String(10), nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(50))  # patent/trademark/design
    status: Mapped[str | None] = mapped_column(String(30))
    deadline: Mapped[date | None] = mapped_column(Date)
    attorney_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    parties: Mapped[list["Party"]] = relationship("Party", back_populates="case")
    mail_messages: Mapped[list["MailMessage"]] = relationship(  # noqa: F821
        "MailMessage", back_populates="case"
    )
    draft_responses: Mapped[list["DraftResponse"]] = relationship(  # noqa: F821
        "DraftResponse", back_populates="case"
    )


class Party(Base):
    __tablename__ = "parties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE")
    )
    name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(50))  # client/opponent_agent/inventor/internal
    org_name: Mapped[str | None] = mapped_column(String(200))

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="parties")
