from app.templates.mail_templates import get_template_for_mail

SYSTEM_PROMPT = """당신은 특허법인 아이피랩(IP LAB Patent Law Firm)의 메일 회신 전문 AI입니다.
수신 메일과 사건 정보를 바탕으로 실무에 바로 사용할 수 있는 회신 초안을 작성합니다.

[사무소 기본 정보]
- 사무소명: IP LAB Patent Law Firm (특허법인 아이피랩)
- 주소: 5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea
- TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
- 웹사이트: https://en.ip-lab.co.kr/

[수발신 유형 분류]
발신 유형 (상황별 적용):
  A. 영문 단순 수신 확인: 연차료·갱신료·공지 등 → "We acknowledge receipt of your e-mail below with thanks."
  B. OA 완료보고·비용청구: 의견서/보정서 제출 후 고객에게 → 서지사항 테이블 + 청구서 동봉 안내
  C. 출원완료 보고: 출원 접수 후 → 출원번호·일자 포함 보고
  D. 비용견적 리마인더: 미회신 시 → REMINDER 제목 + Your ref / Our ref 포함
  E. 내부 사건수임 알림: 신규 수임 → 사건 테이블 형식
  F. GPOA/위임장 안내: 외국 대리인 질의 → 번호 매긴 답변 형식

수신 유형 (회신 방향 결정):
  1. OA 대응 요청 → 접수 확인 후 마감일 내 완료 약속
  2. 초안(Draft) 수신 → 검토 일정 회신
  3. 연차료 알림 → 단순 수신 확인 (고객 승인 필요시 별도 문의)
  4. 비용 견적 요청 → 검토 후 회신 약속
  5. 도면 의뢰 → 수신 확인 및 작업 일정 안내

[작성 규칙]
1. 국문(draft_ko)과 영문(draft_en) 초안을 모두 작성
2. 제공된 템플릿 참고 문구가 있으면 해당 문체·구조를 그대로 따를 것
3. 수신 메일의 핵심 질문/요청 사항을 모두 다룰 것
4. 불확실한 내용은 [확인 필요] 표시를 남길 것
5. 마감일이 있는 경우 반드시 초안에 언급
6. 수신자 추천: 역할(to/cc)과 이유를 명확히 제시
7. 초안은 완성된 메일 형식 (인사말 → 본문 → 맺음말 → 서명)으로 작성
8. 영문 서명란은 항상 IP LAB 사무소 정보 포함"""


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

    # 수신 메일과 매칭되는 실무 템플릿 힌트 — 사건 DB 값으로 변수 치환 후 포함
    subject = mail_data.get("subject", "")
    matched = get_template_for_mail(subject, body_preview, direction="inbound")
    template_section = ""
    if matched:
        from app.templates.resolver import resolve_template
        reply_guide = matched.get("reply_guide", "")
        template_section = f"""
[매칭된 실무 템플릿: {matched['name']}]
처리 가이드:
{reply_guide}
"""
        auto_ko = matched.get("auto_reply_ko", "")
        auto_en = matched.get("auto_reply_en", "")
        mail_info = {"from_name": mail_data.get("from_name"), "from_email": mail_data.get("from_email")}

        if auto_ko:
            resolved_ko = resolve_template(auto_ko, case_info=case_info, mail_info=mail_info, language="ko")
            template_section += f"\n참고 초안(국문) — [확인 필요] 항목을 채워 완성하세요:\n{resolved_ko}\n"
        if auto_en:
            resolved_en = resolve_template(auto_en, case_info=case_info, mail_info=mail_info, language="en")
            template_section += f"\n참고 초안(영문) — [확인 필요] 항목을 채워 완성하세요:\n{resolved_en}\n"

        # 권장 회신 템플릿(outbound)이 있으면 그것도 사건 정보로 치환해서 제공
        reply_tpl_id = matched.get("reply_template_id")
        if reply_tpl_id and case_info:
            from app.templates.mail_templates import OUTBOUND_BY_ID
            reply_tpl = OUTBOUND_BY_ID.get(reply_tpl_id)
            if reply_tpl:
                reply_body, reply_meta = reply_tpl
                lang = reply_meta.get("language", "ko")
                resolved_reply = resolve_template(reply_body, case_info=case_info, mail_info=mail_info, language=lang)
                template_section += (
                    f"\n[권장 발신 템플릿: {reply_meta['name']}]\n"
                    f"사건 정보 자동 완성 결과 ([확인 필요] 항목 직접 수정 필요):\n{resolved_reply[:800]}\n"
                )

    return f"""다음 메일에 대한 회신 초안을 작성해주세요.

원본 메일:
발신자: {mail_data.get('from_email')} ({mail_data.get('from_name')})
제목: {subject}
본문:
{body_preview}
{case_section}{analysis_section}{history_section}{template_section}
위 정보를 바탕으로 국문/영문 회신 초안과 수신자 추천을 JSON 스키마에 맞게 반환하세요."""
