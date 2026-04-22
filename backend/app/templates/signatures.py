"""
발신자별 서명 정의
실제 메일 서명 패턴 기반 (Outlook OST 분석)

구조:
  - 파트너: 직접 서명
  - 매니저/직원: on behalf of 파트너 서명
"""

# 파트너 정보 (영문 서명에 사용)
_PARTNERS = {
    "dikim@ip-lab.co.kr": {
        "name_en": "DONG-IL KIM",
        "title_en": "Chief Managing Partner / Patent Attorney",
        "gender": "Mr.",
    },
    "mrkim@ip-lab.co.kr": {
        "name_en": "MI-RYEONG KIM",
        "title_en": "Partner / Patent Attorney",
        "gender": "Ms.",
    },
    "jhwoo@ip-lab.co.kr": {
        "name_en": "JAE-HYUNG WOO",
        "title_en": "Partner / Patent Attorney",
        "gender": "Mr.",
    },
    "mspark@ip-lab.co.kr": {
        "name_en": "MINSOO PARK",
        "title_en": "Partner / Patent Attorney",
        "gender": "Mr.",
    },
}

# 직원별 서명 정의
# dept_partner: 해당 직원이 "on behalf of" 할 파트너 이메일
_STAFF_META = {
    # 해외관리팀
    "jelee@ip-lab.co.kr":  {"name_ko": "이정은", "name_en": "JUNG-EUN LEE",  "gender": "Ms.", "title_ko": "주임",    "title_en": "IP Manager",       "dept": "해외관리", "dept_partner": "jhwoo@ip-lab.co.kr"},
    "gekim@ip-lab.co.kr":  {"name_ko": "이가은", "name_en": "GAEUN KIM",     "gender": "Ms.", "title_ko": "과장",    "title_en": "IP Manager",       "dept": "해외관리", "dept_partner": "mrkim@ip-lab.co.kr"},
    # 국내관리팀
    "kohwang@ip-lab.co.kr":{"name_ko": "황광옥", "name_en": "KWANGOK HWANG", "gender": "Ms.", "title_ko": "팀장",    "title_en": "Case Manager",     "dept": "국내관리", "dept_partner": "dikim@ip-lab.co.kr"},
    "hjna@ip-lab.co.kr":   {"name_ko": "나해지", "name_en": "HAEJI NA",      "gender": "Ms.", "title_ko": "주임",    "title_en": "Case Manager",     "dept": "국내관리", "dept_partner": "dikim@ip-lab.co.kr"},
    "mjkim@ip-lab.co.kr":  {"name_ko": "김민지", "name_en": "MINJI KIM",     "gender": "Ms.", "title_ko": "대리",    "title_en": "Case Manager",     "dept": "국내관리", "dept_partner": "dikim@ip-lab.co.kr"},
    # 특허1부
    "jwshin@ip-lab.co.kr": {"name_ko": "신지원", "name_en": "JIWON SHIN",    "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    "jhyou@ip-lab.co.kr":  {"name_ko": "유재호", "name_en": "JAEHO YOO",     "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    "jykim@ip-lab.co.kr":  {"name_ko": "김주윤", "name_en": "JOOYOON KIM",   "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    "sjlee@ip-lab.co.kr":  {"name_ko": "이성재", "name_en": "SUNGJAE LEE",   "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    "jylee@ip-lab.co.kr":  {"name_ko": "이주연", "name_en": "JOOYEON LEE",   "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    "sjang@ip-lab.co.kr":  {"name_ko": "장솔",   "name_en": "SOL JANG",      "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허1부", "dept_partner": "mspark@ip-lab.co.kr"},
    # 특허2부
    "chjeong@ip-lab.co.kr":{"name_ko": "정채현", "name_en": "CHAEHYUN JEONG","gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허2부", "dept_partner": "jhwoo@ip-lab.co.kr"},
    "yacho@ip-lab.co.kr":  {"name_ko": "조윤아", "name_en": "YOONA CHO",     "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허2부", "dept_partner": "jhwoo@ip-lab.co.kr"},
    "dhkim@ip-lab.co.kr":  {"name_ko": "김도희", "name_en": "DOHUI KIM",     "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허2부", "dept_partner": "jhwoo@ip-lab.co.kr"},
    # 특허3부
    "mslee@ip-lab.co.kr":  {"name_ko": "이민식", "name_en": "MINSIK LEE",    "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "wycho@ip-lab.co.kr":  {"name_ko": "조운영", "name_en": "WOONYOUNG CHO", "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "yjhwang@ip-lab.co.kr":{"name_ko": "황윤지", "name_en": "YUNJI HWANG",   "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "ujkim@ip-lab.co.kr":  {"name_ko": "김유진", "name_en": "YUJIN KIM",     "gender": "Ms.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "shoh@ip-lab.co.kr":   {"name_ko": "오세현", "name_en": "SEHYUN OH",     "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "jpkim@ip-lab.co.kr":  {"name_ko": "김준표", "name_en": "JUNPYO KIM",    "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "shbae@ip-lab.co.kr":  {"name_ko": "배상혁", "name_en": "SANGHYUK BAE",  "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "mwlee@ip-lab.co.kr":  {"name_ko": "이민우", "name_en": "MINWOO LEE",    "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "sychoi@ip-lab.co.kr": {"name_ko": "최수연", "name_en": "SOOYEON CHOI",  "gender": "Ms.", "title_ko": "사원",    "title_en": "Staff",            "dept": "특허3부", "dept_partner": "mrkim@ip-lab.co.kr"},
    "dylee@ip-lab.co.kr":  {"name_ko": "이동영", "name_en": "DONGYOUNG LEE", "gender": "Mr.", "title_ko": "변리사",  "title_en": "Patent Attorney",  "dept": "특허2부", "dept_partner": "jhwoo@ip-lab.co.kr"},
}

_FIRM_EN = (
    "\n\nIP LAB Patent Law Firm (특허법인 아이피랩)\n"
    "5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea\n"
    "TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825\n"
    "WEBSITE: https://en.ip-lab.co.kr/"
)

_FIRM_KO = (
    "\n\n특허법인 아이피랩\n"
    "서울특별시 강서구 마곡동로 55, MARCUS 5층\n"
    "TEL: 02-6925-4821 | FAX: 02-6925-4825\n"
    "WEBSITE: https://ip-lab.co.kr/"
)

_DISCLAIMER = (
    "\n\nThis message is intended only for the designated recipient(s). "
    "It may contain confidential or proprietary information and may be subject to "
    "attorney-client privilege or other confidentiality protections. "
    "If you are not a designated recipient, please notify the sender immediately "
    "and destroy all copies."
)


def _build_en(email: str) -> str:
    """영문 서명 생성"""
    if email in _PARTNERS:
        p = _PARTNERS[email]
        return f"\nBest regards,\n\n{p['name_en']}\n{p['title_en']}{_FIRM_EN}{_DISCLAIMER}"

    if email not in _STAFF_META:
        return f"\nBest regards,\n\nIP LAB Patent Law Firm{_FIRM_EN}{_DISCLAIMER}"

    s = _STAFF_META[email]
    partner_email = s.get("dept_partner", "dikim@ip-lab.co.kr")
    p = _PARTNERS.get(partner_email, _PARTNERS["dikim@ip-lab.co.kr"])

    return (
        f"\nBest regards,\n\n"
        f"{s['name_en']} ({s['gender']}) / {s['title_en']}\n\n"
        f"on behalf of\n\n"
        f"{p['name_en']} ({p['gender']}) / {p['title_en']}"
        f"{_FIRM_EN}{_DISCLAIMER}"
    )


def _build_ko(email: str) -> str:
    """국문 서명 생성"""
    if email in _PARTNERS:
        p = _PARTNERS[email]
        return f"\n감사합니다.\n\n{p['name_en']} ({p['title_en']})\n특허법인 아이피랩{_FIRM_KO}"

    if email not in _STAFF_META:
        return f"\n감사합니다.\n\n특허법인 아이피랩{_FIRM_KO}"

    s = _STAFF_META[email]
    partner_email = s.get("dept_partner", "dikim@ip-lab.co.kr")
    p = _PARTNERS.get(partner_email, _PARTNERS["dikim@ip-lab.co.kr"])

    return (
        f"\n감사합니다.\n\n"
        f"{s['name_ko']} {s['title_ko']}\n"
        f"(담당 파트너: {p['name_en']})\n"
        f"특허법인 아이피랩 {s['dept']}{_FIRM_KO}"
    )


def get_signatures_for_user(email: str) -> list[dict]:
    """
    발신자 이메일 기준 사용 가능한 서명 목록 반환.
    - 본인 서명 (기본)
    - 파트너 직접 서명 (파트너인 경우)
    - on behalf of 서명 (직원인 경우)
    """
    sigs = []

    # 파트너: 직접 서명
    if email in _PARTNERS:
        p = _PARTNERS[email]
        sigs.append({
            "id": f"{email}__direct_en",
            "label": f"{p['name_en']} (영문)",
            "language": "en",
            "sender_email": email,
            "body": _build_en(email),
            "is_default": True,
        })
        sigs.append({
            "id": f"{email}__direct_ko",
            "label": f"{p['name_en']} (국문)",
            "language": "ko",
            "sender_email": email,
            "body": _build_ko(email),
            "is_default": False,
        })
        return sigs

    # 직원: on behalf of 서명
    if email in _STAFF_META:
        s = _STAFF_META[email]
        partner_email = s.get("dept_partner", "dikim@ip-lab.co.kr")
        p = _PARTNERS.get(partner_email, _PARTNERS["dikim@ip-lab.co.kr"])

        sigs.append({
            "id": f"{email}__behalf_en",
            "label": f"{s['name_en']} on behalf of {p['name_en']} (영문)",
            "language": "en",
            "sender_email": email,
            "body": _build_en(email),
            "is_default": True,
        })
        sigs.append({
            "id": f"{email}__behalf_ko",
            "label": f"{s['name_ko']} {s['title_ko']} (국문)",
            "language": "ko",
            "sender_email": email,
            "body": _build_ko(email),
            "is_default": False,
        })
        # 파트너 직접 서명도 선택 가능하게 제공
        sigs.append({
            "id": f"{partner_email}__direct_en",
            "label": f"{p['name_en']} 직접 서명 (영문)",
            "language": "en",
            "sender_email": partner_email,
            "body": _build_en(partner_email),
            "is_default": False,
        })
        return sigs

    # 알 수 없는 발신자: 기본 사무소 서명
    sigs.append({
        "id": "default_en",
        "label": "IP LAB 기본 서명 (영문)",
        "language": "en",
        "sender_email": email,
        "body": _build_en(email),
        "is_default": True,
    })
    sigs.append({
        "id": "default_ko",
        "label": "IP LAB 기본 서명 (국문)",
        "language": "ko",
        "sender_email": email,
        "body": _build_ko(email),
        "is_default": False,
    })
    return sigs
