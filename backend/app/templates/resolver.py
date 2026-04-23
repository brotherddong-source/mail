"""
템플릿 변수 치환 엔진

우선순위:
  1. 사건 DB (case_info) — our_ref, your_ref, app_number, client_name, deadline 등
  2. 수신 메일 (mail_info) — recipient_name(발신자명), from_email
  3. 발신자 (sender_email)
  4. 오늘 날짜 — submission_date, recv_date
  알 수 없는 변수 → [확인 필요: var_name]
"""

from datetime import date


class _SafeDict(dict):
    """누락 키에 대해 KeyError 대신 [확인 필요: key] 반환"""
    def __missing__(self, key: str) -> str:
        return f"[확인 필요: {key}]"


def resolve_template(
    template_body: str,
    case_info: dict | None = None,
    mail_info: dict | None = None,
    sender_email: str | None = None,
    language: str = "ko",
) -> str:
    """
    템플릿 문자열의 {var} 자리에 실제 값을 채워 반환.
    알 수 없는 변수는 [확인 필요: var_name] 으로 표시.
    """
    v = _SafeDict()

    # ── 날짜 기본값 ──────────────────────────────────────────────
    today_str = date.today().strftime("%Y-%m-%d")
    v["today"] = today_str
    v["submission_date"] = today_str
    v["recv_date"] = today_str

    # ── 사건 DB ─────────────────────────────────────────────────
    if case_info:
        v["our_ref"] = case_info.get("case_number") or ""
        v["your_ref"] = case_info.get("your_ref") or ""
        v["app_number"] = case_info.get("app_number") or ""
        v["client_name"] = case_info.get("client_name") or ""
        v["client"] = v["client_name"]
        v["applicant"] = case_info.get("applicant") or v["client_name"]
        v["applicants"] = v["applicant"]
        v["country"] = case_info.get("country") or ""
        v["deadline"] = case_info.get("deadline") or ""
        v["due_date"] = v["deadline"]
        v["filing_date"] = case_info.get("filed_at") or ""
        v["notes"] = case_info.get("notes") or ""
        v["attorney"] = case_info.get("attorney") or ""
        v["attorney_name"] = v["attorney"]
        v["assignee"] = v["attorney"]
        v["status"] = case_info.get("status") or ""
        v["kr_ref"] = v["our_ref"]  # 국내 KR ref와 our_ref는 대부분 동일

        # 특허 날짜 필드
        v["priority_date"] = case_info.get("priority_date") or ""
        v["public_notice_exception_date"] = case_info.get("public_notice_exception_date") or ""
        v["exam_request_date"] = case_info.get("exam_request_date") or ""
        v["exam_request_deadline"] = case_info.get("exam_request_deadline") or ""
        v["published_at"] = case_info.get("published_at") or ""
        v["intl_filed_at"] = case_info.get("intl_filed_at") or ""
        v["national_phase_at"] = case_info.get("national_phase_at") or ""
        v["registered_at"] = case_info.get("registered_at") or ""

        # 제목: 언어별로 분기
        if language == "en":
            v["title"] = case_info.get("title_en") or case_info.get("title_ko") or ""
            v["matter_title"] = v["title"]
        else:
            v["title"] = case_info.get("title_ko") or case_info.get("title_en") or ""
            v["matter_title"] = case_info.get("title_en") or v["title"]

    # ── 수신 메일 정보 ───────────────────────────────────────────
    if mail_info:
        v["recipient_name"] = mail_info.get("from_name") or mail_info.get("from_email") or ""
        v["our_name"] = "IP LAB Patent Law Firm (특허법인 아이피랩)"

    # ── 발신자 정보 ──────────────────────────────────────────────
    if sender_email:
        v["sender_email"] = sender_email

    # ── 수동 입력 필요 항목 — 빈 문자열로 남기면 AI가 채움 ───────
    # (SafeDict가 누락 키를 [확인 필요]로 처리하므로 여기서 정의 안 해도 되지만,
    #  명시적으로 나열해 어떤 변수들이 수동 필요한지 문서화)
    manual_required = [
        "inventors", "priority_info", "priority_app_no", "priority_date",
        "attachment_count", "review_deadline", "kipo_table_rows", "overseas_table_rows",
        "drawing_type", "drawing_details", "revision_items", "doc_type",
        "mgmt_no", "main_inventor", "is_public", "is_joint", "is_research",
        "numbered_responses", "sender_name", "sender_title", "gender_title",
        "partner_name", "partner_gender", "partner_title", "sender_dept",
        "ext", "attorney_email", "attorney_tel", "kr_ref",
    ]
    for key in manual_required:
        if key not in v:
            # 비워두면 AI가 문맥에서 채움
            pass  # SafeDict.__missing__ 이 [확인 필요] 반환

    try:
        return template_body.format_map(v)
    except Exception:
        return template_body  # 포맷 실패 시 원본 반환


def get_resolved_vars(
    case_info: dict | None,
    mail_info: dict | None = None,
    sender_email: str | None = None,
    language: str = "ko",
) -> dict:
    """템플릿 없이 변수 dict만 필요할 때 사용 (프리뷰용)"""
    v = _SafeDict()
    resolve_template("", case_info=case_info, mail_info=mail_info,
                     sender_email=sender_email, language=language)
    return dict(v)
