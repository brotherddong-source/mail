"""
Claude API 기반 회신 초안 생성 엔진
입력: 수신 메일 + 사건 정보 + 과거 관련 메일 히스토리 (최대 5건)
출력: DraftReplyResult (국문/영문 초안, 수신자 추천)
"""
import logging

import anthropic

from app.ai.prompts.draft import SYSTEM_PROMPT, build_draft_prompt
from app.ai.schemas import DraftReplyResult
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


class MailDrafter:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def draft(
        self,
        mail_data: dict,
        analysis: dict,
        case_info: dict | None = None,
        mail_history: list[dict] | None = None,
    ) -> DraftReplyResult:
        """
        회신 초안 생성.
        analysis: MailAnalysisResult.model_dump()
        mail_history: 과거 관련 메일 목록 (최대 5건)
        """
        user_prompt = build_draft_prompt(
            mail_data=mail_data,
            analysis=analysis,
            case_info=case_info,
            mail_history=mail_history,
        )

        try:
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[
                    {
                        "name": "draft_reply",
                        "description": "회신 초안을 구조화된 형식으로 반환",
                        "input_schema": DraftReplyResult.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": "draft_reply"},
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "draft_reply":
                    return DraftReplyResult.model_validate(block.input)

            raise RuntimeError("AI 응답에서 초안 결과를 찾을 수 없습니다.")

        except anthropic.APIError as e:
            logger.error("Claude API 오류 (초안 생성): %s", e)
            raise
