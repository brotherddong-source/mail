SYSTEM_PROMPT = """당신은 특허사무소의 메일 회신 전문 AI입니다.
수신 메일과 사건 정보를 바탕으로 전문적인 회신 초안을 작성합니다.

규칙:
1. 국문(draft_ko)과 영문(draft_en) 초안을 모두 작성
2. 특허 업무에 적합한 공식적이고 전문적인 문체 사용
3. 수신 메일의 핵심 질문/요청 사항을 모두 다룰 것
4. 불확실한 내용은 초안에 [확인 필요] 표시를 남길 것
5. 마감일이 있는 경우 반드시 언급
6. 수신자 추천 시 역할(to/cc)과 이유를 명확히 제시
7. 초안은 완성된 메일 형식 (인사말 → 본문 → 맺음말)으로 작성"""


def build_draft_prompt(
    mail_data: dict,
    analysis: dict,
    case_info: dict | None = None,
    mail_history: list[dict] | None = None,
) -> str:
    case_section = ""
    if case_info:
        case_section = f"""
사건 정보:
- 사건번호: {case_info.get('case_number', '-')}
- 고객사: {case_info.get('client_name', '-')}
- 국가: {case_info.get('country', '-')}
- 사건 유형: {case_info.get('case_type', '-')}
- 상태: {case_info.get('status', '-')}
- 마감일: {case_info.get('deadline', '-')}
"""

    history_section = ""
    if mail_history:
        history_section = "\n과거 관련 메일 (최근 순):\n"
        for i, h in enumerate(mail_history[:5], 1):
            history_section += f"""
[{i}] 발신: {h.get('from_email')} | 수신일: {h.get('received_at')}
제목: {h.get('subject')}
요약: {h.get('ai_summary', '(요약 없음)')}
"""

    analysis_section = f"""
AI 분석 결과:
- 분류: {analysis.get('classification')}
- 우선순위: {analysis.get('urgency')}
- 핵심 포인트: {', '.join(analysis.get('key_points', []))}
- 마감일 탐지: {analysis.get('deadline_detected', '없음')}
- 주의사항: {', '.join(analysis.get('review_warnings', []))}
"""

    body_preview = (mail_data.get("body_text") or "")[:2000]

    return f"""다음 메일에 대한 회신 초안을 작성해주세요.

원본 메일:
발신자: {mail_data.get('from_email')} ({mail_data.get('from_name')})
제목: {mail_data.get('subject')}
본문:
{body_preview}
{case_section}{analysis_section}{history_section}
위 정보를 바탕으로 국문/영문 회신 초안과 수신자 추천을 JSON 스키마에 맞게 반환하세요."""
