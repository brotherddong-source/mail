import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 식별
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # OurRef
    your_ref: Mapped[str | None] = mapped_column(String(100))                          # YourRef
    app_number: Mapped[str | None] = mapped_column(String(100))                        # 출원번호
    reg_number: Mapped[str | None] = mapped_column(String(100))                        # 등록번호
    intl_app_number: Mapped[str | None] = mapped_column(String(100))                   # 국제출원번호

    # 명칭
    title_ko: Mapped[str | None] = mapped_column(Text)   # 국문명칭
    title_en: Mapped[str | None] = mapped_column(Text)   # 영문명칭

    # 고객
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)   # 의뢰인
    client_domain: Mapped[str | None] = mapped_column(String(100))          # 이메일 도메인 매칭용
    applicant: Mapped[str | None] = mapped_column(String(200))              # 출원인
    applicant_contact: Mapped[str | None] = mapped_column(String(100))      # 출원인담당자

    # 분류
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="KR")
    division: Mapped[str | None] = mapped_column(String(10))     # 구분 (내국/해외)
    case_type: Mapped[str | None] = mapped_column(String(50))    # 권리 (특허/상표/디자인)
    app_category: Mapped[str | None] = mapped_column(String(50)) # 출원구분
    app_kind: Mapped[str | None] = mapped_column(String(50))     # 출원종류

    # 담당
    attorney: Mapped[str | None] = mapped_column(String(50))     # 담당변리사
    department: Mapped[str | None] = mapped_column(String(50))   # 부서

    # 상태/마감
    status: Mapped[str | None] = mapped_column(String(50))       # 현재상태
    deadline: Mapped[date | None] = mapped_column(Date)          # 사건마감일
    app_deadline: Mapped[date | None] = mapped_column(Date)      # 출원마감일
    reg_deadline: Mapped[date | None] = mapped_column(Date)      # 등록마감일
    annual_deadline: Mapped[date | None] = mapped_column(Date)   # 연차마감일

    # 날짜
    filed_at: Mapped[date | None] = mapped_column(Date)          # 출원일
    registered_at: Mapped[date | None] = mapped_column(Date)     # 등록일
    received_at: Mapped[date | None] = mapped_column(Date)       # 접수일

    # 기타
    ipc: Mapped[str | None] = mapped_column(String(100))         # IPC분류
    notes: Mapped[str | None] = mapped_column(Text)              # 비고

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
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(50))
    org_name: Mapped[str | None] = mapped_column(String(200))

    case: Mapped["Case | None"] = relationship("Case", back_populates="parties")
