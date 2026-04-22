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
# ----------------------------------------------------------------

# IP LAB 내부 사건번호 패턴 (Our Ref)
# 실제 사용 예: PL24125PCEP, PM23188PCJP, PNN25208JP5, PU26144KR,
#              PII260900PCN, DI26004CN, LM25009KR, FCI26KR00098
# 규칙: 영문 2~4자 + 숫자 2~4자 + 영숫자 후미 (국가코드·PCT코드 포함)
# 단, PCT 슬래시 구성요소(예: KR2024)와 공식 출원번호 접두어(EP/CN/US)는 제외
_IPLAB_OUR_REF = re.compile(
    r"(?<![/\-])"                               # PCT·하이픈 구성요소 제외
    r"\b"
    r"(?!EP\d|CN\d|US\d)"                       # 공식 출원번호 접두어 제외
    r"([A-Z]{2,4}\d{2,4}[A-Z0-9]{0,10}(?:PC[A-Z]{2,4})?\d{0,4})"
    r"\b",
)

# Your Ref 패턴 — 외국 대리인마다 형식이 달라 단독 신뢰 불가.
# Our Ref와 함께 등장할 때만 보조로 사용.
_YOUR_REF_LABEL = re.compile(
    r"(?:Your\s*Ref\.?|YourRef)\s*[:：]?\s*([A-Z0-9\-/\.]{4,30})",
    re.IGNORECASE,
)

CASE_NUMBER_PATTERNS = [
    # ── IP LAB 내부 Our Ref (최우선 — DB case_number와 1:1 매칭) ──
    # "Our Ref.: PL24125PCEP" / "Our Ref: PM23188PCJP" 형태
    re.compile(
        r"(?:Our\s*Ref\.?|OurRef)\s*[:：]?\s*"
        r"([A-Z]{2,4}\d{2,4}[A-Z0-9]{0,10}(?:PC[A-Z]{2,4})?\d{0,4})",
        re.IGNORECASE,
    ),
    # ── 한국 출원번호: 10-2024-0012345 (뒤에 한글 '호' 등이 붙어도 인식) ──
    re.compile(r"\b(1[0-9]-\d{4}-\d{7})"),
    # ── PCT 출원번호: PCT/KR2024/001234 ──
    re.compile(r"\b(PCT/[A-Z]{2}\d{4}/\d{6})\b"),
    # ── 유럽 출원번호: EP24123456.7 (점 포함) → 점 없는 패턴은 뒤에 .숫자가 없을 때만 ──
    re.compile(r"\b(EP\s*\d{8}\.\d)\b"),
    re.compile(r"\b(EP\s*\d{8})(?!\.\d)\b"),
    # ── 미국 출원번호: 17/123,456 ──
    re.compile(r"\b(\d{2}/\d{3},?\d{3})\b"),
    # ── 중국 출원번호: CN202410123456 ──
    re.compile(r"\b(CN\d{12,15})\b"),
    # ── 일본 출원번호: 特願2024-123456 ──
    re.compile(r"特願(\d{4}-\d+)"),
    # ── Our Ref 라벨 없이 단독 등장하는 IP LAB 형식 (보조 — 오탐 가능성 있음) ──
    _IPLAB_OUR_REF,
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
        """
        텍스트에서 사건번호 후보 추출.
        Our Ref 라벨이 붙은 값을 앞쪽에 배치해 매칭 우선순위를 높임.
        """
        # Our Ref 라벨 명시 → 가장 신뢰도 높음
        labeled: list[str] = CASE_NUMBER_PATTERNS[0].findall(text)
        # 나머지 패턴
        others: list[str] = []
        for pattern in CASE_NUMBER_PATTERNS[1:]:
            others.extend(pattern.findall(text))
        # 공백 정규화 (EP 24843562.0 → EP24843562.0)
        all_refs = [r.replace(" ", "") for r in labeled + others]
        return list(dict.fromkeys(all_refs))  # 순서 유지 중복 제거

    def _extract_domain(self, email: str) -> str | None:
        """이메일에서 도메인 추출 (무료 메일 서비스 제외)"""
        FREE_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "naver.com", "daum.net"}
        if "@" not in email:
            return None
        domain = email.split("@")[-1].lower()
        return None if domain in FREE_DOMAINS else domain
