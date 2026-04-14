"""
Claude API 기반 메일 분석 엔진
- 분류 / 요약 / 번역 / 마감 탐지
- 민감정보 마스킹 옵션
"""
import json
import logging
import re

import anthropic

from app.ai.prompts.analyze import SYSTEM_PROMPT, build_analyze_prompt
from app.ai.schemas import MailAnalysisResult
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 민감정보 마스킹 패턴
_MASK_PATTERNS = [
    (re.compile(r"\b\d{6}-\d{7}\b"), "[주민번호]"),           # 주민등록번호
    (re.compile(r"\b\d{3}-\d{4}-\d{4}\b"), "[전화번호]"),      # 전화번호
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[이메일]"),
]

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048


class MailAnalyzer:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _mask_sensitive(self, text: str) -> str:
        """민감정보 마스킹"""
        for pattern, replacement in _MASK_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    async def analyze(
        self,
        mail_data: dict,
        case_info: dict | None = None,
        mask_sensitive: bool = True,
    ) -> MailAnalysisResult:
        """
        메일을 분석하여 MailAnalysisResult 반환.
        mask_sensitive=True이면 발송 전 민감정보 마스킹 적용.
        """
        if mask_sensitive:
            mail_data = {
                **mail_data,
                "body_text": self._mask_sensitive(mail_data.get("body_text") or ""),
                "subject": self._mask_sensitive(mail_data.get("subject") or ""),
            }

        user_prompt = build_analyze_prompt(mail_data, case_info)

        try:
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[
                    {
                        "name": "mail_analysis",
                        "description": "메일 분석 결과를 구조화된 형식으로 반환",
                        "input_schema": MailAnalysisResult.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": "mail_analysis"},
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "mail_analysis":
                    return MailAnalysisResult.model_validate(block.input)

            raise RuntimeError("AI 응답에서 분석 결과를 찾을 수 없습니다.")

        except anthropic.APIError as e:
            logger.error("Claude API 오류: %s", e)
            raise
