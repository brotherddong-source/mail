"""
사건 매칭 엔진
우선순위:
  1. 제목/본문 사건번호 정규식 매칭     (confidence: 0.95)
  2. conversation_id 스레드 연속성       (confidence: 0.90)
  3. 발신자 이메일 → Party 직접 매칭    (confidence: 0.85)
  4. 발신자 도메인 → 고객사 매칭        (confidence: 0.70)
  5. 과거 동일 발신자 사건 이력         (confidence: 0.50)
"""
import logging
import re
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.cases.models import Case
from app.domain.cases.repository import CaseRepository

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# 사건번호 패턴 (특허사무소 내부 번호 및 공식 출원번호 형식)
# 필요 시 추가/수정
# ----------------------------------------------------------------
CASE_NUMBER_PATTERNS = [
    # 내부 사건번호: KR-2024-00123, JP-2023-P-001
    re.compile(r"\b([A-Z]{2}-\d{4}-[A-Z0-9-]{3,15})\b"),
    # 한국 출원번호: 10-2024-0012345
    re.compile(r"\b(1[0-9]-\d{4}-\d{7})\b"),
    # 미국 출원번호: 17/123,456 또는 US17/123456
    re.compile(r"\b(?:US)?(\d{2}/\d{3},?\d{3})\b"),
    # PCT 출원번호: PCT/KR2024/001234
    re.compile(r"\b(PCT/[A-Z]{2}\d{4}/\d{6})\b"),
    # 유럽 출원번호: EP24123456
    re.compile(r"\b(EP\d{8})\b"),
    # 일본 출원번호: 特願2024-123456
    re.compile(r"特願(\d{4}-\d+)"),
    # 중국 출원번호: CN202410123456
    re.compile(r"\b(CN\d{12,15})\b"),
]


@dataclass
class MatchResult:
    matched_case: Case | None
    confidence_score: float  # 0.0 ~ 1.0
    match_reason: str
    detected_case_numbers: list[str]


class CaseMatcher:
    def __init__(self, db: AsyncSession):
        self.repo = CaseRepository(db)

    async def match(
        self,
        subject: str,
        body_text: str,
        from_email: str,
        conversation_id: str | None = None,
    ) -> MatchResult:
        """메일로부터 가장 적합한 사건을 찾아 반환"""
        text = f"{subject}\n{body_text}"
        detected_numbers = self._extract_case_numbers(text)

        # 1순위: 사건번호 정규식 매칭
        for number in detected_numbers:
            case = await self.repo.get_by_case_number(number)
            if case:
                logger.info("사건 매칭 (사건번호): %s → %s", number, case.id)
                return MatchResult(
                    matched_case=case,
                    confidence_score=0.95,
                    match_reason=f"사건번호 직접 매칭: {number}",
                    detected_case_numbers=detected_numbers,
                )

        # 2순위: conversation_id 스레드 연속성
        if conversation_id:
            case = await self.repo.find_by_conversation(conversation_id)
            if case:
                logger.info("사건 매칭 (스레드): conversation=%s → %s", conversation_id, case.id)
                return MatchResult(
                    matched_case=case,
                    confidence_score=0.90,
                    match_reason=f"동일 대화 스레드 연속성: {conversation_id}",
                    detected_case_numbers=detected_numbers,
                )

        # 3순위: 발신자 이메일 → Party 직접 매칭
        from_email_lower = from_email.lower()
        cases = await self.repo.find_by_party_email(from_email_lower)
        if len(cases) == 1:
            logger.info("사건 매칭 (발신자 이메일): %s → %s", from_email, cases[0].id)
            return MatchResult(
                matched_case=cases[0],
                confidence_score=0.85,
                match_reason=f"발신자 이메일 매칭: {from_email}",
                detected_case_numbers=detected_numbers,
            )

        # 4순위: 발신자 도메인 → 고객사 매칭
        domain = self._extract_domain(from_email_lower)
        if domain:
            domain_cases = await self.repo.find_by_client_domain(domain)
            if len(domain_cases) == 1:
                logger.info("사건 매칭 (도메인): %s → %s", domain, domain_cases[0].id)
                return MatchResult(
                    matched_case=domain_cases[0],
                    confidence_score=0.70,
                    match_reason=f"발신자 도메인 매칭: {domain}",
                    detected_case_numbers=detected_numbers,
                )

        # 5순위: 과거 동일 발신자 사건 이력 (가장 최근 1건)
        history_cases = await self.repo.find_recent_by_sender(from_email_lower, limit=1)
        if history_cases:
            logger.info("사건 매칭 (이력): %s → %s", from_email, history_cases[0].id)
            return MatchResult(
                matched_case=history_cases[0],
                confidence_score=0.50,
                match_reason=f"과거 발신자 이력 기반 추정: {from_email}",
                detected_case_numbers=detected_numbers,
            )

        logger.info("사건 매칭 실패: from=%s", from_email)
        return MatchResult(
            matched_case=None,
            confidence_score=0.0,
            match_reason="매칭 실패",
            detected_case_numbers=detected_numbers,
        )

    def _extract_case_numbers(self, text: str) -> list[str]:
        """텍스트에서 모든 사건번호 후보 추출"""
        found: list[str] = []
        for pattern in CASE_NUMBER_PATTERNS:
            matches = pattern.findall(text)
            found.extend(matches)
        return list(dict.fromkeys(found))  # 순서 유지 중복 제거

    def _extract_domain(self, email: str) -> str | None:
        """이메일에서 도메인 추출 (무료 메일 서비스 제외)"""
        FREE_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "naver.com", "daum.net"}
        if "@" not in email:
            return None
        domain = email.split("@")[-1].lower()
        return None if domain in FREE_DOMAINS else domain
