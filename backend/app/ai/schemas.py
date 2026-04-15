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


class DraftReplyResult(BaseModel):
    draft_ko: str = Field(description="국문 초안")
    draft_en: str = Field(description="영문 초안")
    suggested_recipients: list[SuggestedRecipient]
    suggested_subject: str = Field(description="회신 제목 제안")
    key_points_addressed: list[str] = Field(description="초안이 다룬 핵심 포인트")
    review_notes: list[str] = Field(description="검토 시 주의사항")
