SYSTEM_PROMPT = """당신은 특허사무소의 메일 분석 전문 AI입니다.
수신된 메일을 분석하여 사건 처리에 필요한 정보를 구조화된 형식으로 추출합니다.

규칙:
1. 요약(summary_ko)은 반드시 한국어로 작성하고, 각 문장을 줄바꿈(\n)으로 구분하여 가독성을 높일 것
2. 원문이 영어인 경우 핵심 내용을 한국어로 번역 (translation_ko 필드), 번역도 단락별로 줄바꿈 포함
3. 특허/상표/디자인 관련 전문 용어를 정확히 인식
4. 마감일, 기한, deadline, due date 관련 표현을 반드시 탐지하여 ISO 날짜로 변환
5. 개인정보 및 기밀 내용을 외부에 노출하지 않음
6. 확실하지 않은 사항은 review_warnings에 포함
7. 사건번호 패턴 (예: KR-2024-XXXXX, 10-2024-XXXXXXX 등)이 보이면 case_number_hint에 포함
8. 발신자가 ip-lab.co.kr 도메인이면 이는 우리 사무소에서 발신한 메일임. 수신 메일로 착각하지 말 것"""


def build_analyze_prompt(mail_data: dict, case_info: dict | None = None) -> str:
    case_context = ""
    if case_info:
        case_context = f"""
관련 사건 정보:
- 사건번호: {case_info.get('case_number', '-')}
- 고객사: {case_info.get('client_name', '-')}
- 국가: {case_info.get('country', '-')}
- 사건 유형: {case_info.get('case_type', '-')}
- 현재 상태: {case_info.get('status', '-')}
- 마감일: {case_info.get('deadline', '-')}
"""

    body_preview = (mail_data.get("body_text") or "")[:3000]

    return f"""다음 메일을 분석해주세요.

발신자: {mail_data.get('from_email', '')} ({mail_data.get('from_name', '')})
수신일시: {mail_data.get('received_at', '')}
제목: {mail_data.get('subject', '')}

본문:
{body_preview}
{case_context}
위 메일을 분석하여 지정된 JSON 스키마에 맞게 결과를 반환하세요."""
