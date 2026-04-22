from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Classification(str, Enum):
    info_only = "info_only"
    requires_reply = "requires_reply"
    internal_review = "internal_review"
    client_forward = "client_forward"
    deadline_critical = "deadline_critical"
    oa_related = "oa_related"
    fee_related = "fee_related"
    document_request = "document_request"
    meeting_schedule = "meeting_schedule"


class SuggestedRecipient(BaseModel):
    email: str
    name: Optional[str] = None
    role: str = Field(description="to 또는 cc")
    reason: str = Field(description="이 수신자를 추천한 이유")


class PriorityInfo(BaseModel):
    app_no: str = Field(description="우선권 출원번호")
    country: str = Field(description="우선권 국가 코드 (KR/US/JP 등)")
    date: Optional[str] = Field(default=None, description="우선권 일자 (YYYY-MM-DD)")


class ForeignAgentRef(BaseModel):
    country: str = Field(description="국가 코드 (JP/CN/EP/US 등)")
    agent: Optional[str] = Field(default=None, description="외국 대리인명")
    their_ref: str = Field(description="외국 대리인의 사건번호 (Your Ref)")


class ExtractedBiblio(BaseModel):
    """메일 본문에서 추출한 서지/레퍼런스 정보 — cases 테이블 업서트에 사용"""
    our_ref: Optional[str] = Field(default=None, description="IP LAB 내부 사건번호 (Our Ref)")
    your_ref: Optional[str] = Field(default=None, description="의뢰인/대리인 사건번호 (Your Ref)")
    app_number: Optional[str] = Field(default=None, description="한국 출원번호")
    intl_app_number: Optional[str] = Field(default=None, description="EP/PCT/JP/CN/US 출원번호")
    title_ko: Optional[str] = Field(default=None, description="발명의 명칭 (국문)")
    title_en: Optional[str] = Field(default=None, description="발명의 명칭 (영문)")
    applicant: Optional[str] = Field(default=None, description="출원인")
    inventors: list[str] = Field(default_factory=list, description="발명자 목록")
    filed_at: Optional[str] = Field(default=None, description="출원일 (YYYY-MM-DD)")
    deadline: Optional[str] = Field(default=None, description="사건 마감일 (YYYY-MM-DD)")
    overseas_deadline: Optional[str] = Field(default=None, description="해외출원마감일 (YYYY-MM-DD)")
    exam_requested: Optional[str] = Field(default=None, description="심사청구 여부 Y/N")
    priority_info: list[PriorityInfo] = Field(default_factory=list, description="우선권 정보 목록")
    foreign_agent_refs: list[ForeignAgentRef] = Field(default_factory=list, description="국가별 외국 대리인 Ref")
    country: Optional[str] = Field(default=None, description="출원 국가 코드")
    attorney: Optional[str] = Field(default=None, description="담당 변리사")


class MailAnalysisResult(BaseModel):
    summary_ko: str = Field(description="한국어 요약 (3~5문장, 각 문장을 줄바꿈으로 구분)")
    translation_ko: Optional[str] = Field(default=None, description="원문이 영어인 경우 한국어 번역")
    classification: Classification
    requires_reply: bool
    reply_reason: Optional[str] = Field(default=None, description="회신이 필요한 이유")
    urgency: Priority
    deadline_detected: Optional[str] = Field(
        default=None, description="탐지된 마감일 (ISO date 형식: YYYY-MM-DD)"
    )
    key_points: list[str] = Field(description="핵심 포인트 리스트")
    case_number_hint: Optional[str] = Field(
        default=None, description="본문에서 탐지된 사건번호"
    )
    review_warnings: list[str] = Field(description="검토 시 주의사항")
    extracted_biblio: Optional[ExtractedBiblio] = Field(
        default=None, description="메일 본문에서 추출한 서지·레퍼런스 정보 (DB 업서트용)"
    )


class DraftReplyResult(BaseModel):
    draft_ko: str = Field(description="국문 초안")
    draft_en: str = Field(description="영문 초안")
    suggested_recipients: list[SuggestedRecipient]
    suggested_subject: str = Field(description="회신 제목 제안")
    key_points_addressed: list[str] = Field(description="초안이 다룬 핵심 포인트")
    review_notes: list[str] = Field(description="검토 시 주의사항")
