"""
실제 발수신 메일 분석으로 도출한 IP LAB 메일 템플릿 모음

수발신 분류:
  OUTBOUND_* : 발신 템플릿 (사무소 → 외부/내부)
  INBOUND_*  : 수신 메일 유형별 → 권장 회신 초안

변수 표기: {변수명}
"""

# ──────────────────────────────────────────────
# OUTBOUND 템플릿 (발신)
# ──────────────────────────────────────────────

OUTBOUND_ACKNOWLEDGE_EN = """\
Dear Sir/Madam:

We acknowledge receipt of your e-mail below with thanks.

Best regards,

{sender_name}
{sender_title}

IP LAB Patent Law Firm (특허법인 아이피랩)
5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea
TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
WEBSITE: https://en.ip-lab.co.kr/
"""
OUTBOUND_ACKNOWLEDGE_EN_META = {
    "id": "outbound_acknowledge_en",
    "name": "영문 수신 확인 회신",
    "category": "acknowledge",
    "language": "en",
    "trigger_keywords": ["acknowledge", "receipt", "RE:", "FW:"],
    "use_case": "외국 대리인·기관으로부터 받은 메일(연차료, 공지, 견적 등)에 대한 표준 수신 확인 회신",
    "variables": ["sender_name", "sender_title"],
}

# ──────────────────────────────────────────────

OUTBOUND_ACKNOWLEDGE_KO = """\
안녕하세요.

하기 메일 잘 수신하였습니다.

감사합니다.

{sender_name} {sender_title}
특허법인 아이피랩
TEL: +82-2-6925-4821
"""
OUTBOUND_ACKNOWLEDGE_KO_META = {
    "id": "outbound_acknowledge_ko",
    "name": "국문 수신 확인 회신",
    "category": "acknowledge",
    "language": "ko",
    "use_case": "국내 고객/내부 직원으로부터 받은 메일의 간단한 수신 확인",
    "variables": ["sender_name", "sender_title"],
}

# ──────────────────────────────────────────────

OUTBOUND_KIPO_NOTICE_LIST = """\
[특허청 통지서수신 알림]

특허청에서 접수한 통지서 내역 및 서류를 전달 드리며, 통지서는 건별로 이지팻 & IPLAB공유폴더에 업로드 됩니다.

[특허청 통지서 확인사항]

1. 당 시스템의 접수일로부터 익일에 일괄적으로 고객에게 보고됩니다.
2. 보고대상제외 등 메모가 필요한 경우: 담당 변리사님은 금일 오후 6시까지 답변 부탁드립니다.
   → 예) 기재불비(보고대상아님/당소부담) / 보고하지않음(당소부담) / 청구서는송부안함 / 직접보고예정

[담당자 지정 메일회신의 경우]
관리팀 담당자를 수신인으로 설정하여 회신요청 부탁드립니다.
** 담당자를 지정해서 알려주시면 네이버웍스 캘린더(할일설정) 담당자 설정됨을 알려드립니다.
** 출원인 보고대상 아닌경우 출원보고없음체크 부탁드립니다.

[국내/심판-통지서수신현황]

발송일 | 접수일 | 마감일 | REF. NO. | 출원번호 | 출원인 | 구분 | 권리 | 접수서류명 | 메모 | 담당변리사 | 담당자 | 출원인보고없음
{kipo_table_rows}

[해외-통지서수신현황]

발송일 | 접수일 | 마감일 | REF. NO. | 출원번호 | 출원인 | 구분 | 권리 | 접수서류명 | 메모 | 담당변리사 | 담당자 | 출원인보고없음
{overseas_table_rows}
"""
OUTBOUND_KIPO_NOTICE_LIST_META = {
    "id": "outbound_kipo_notice_list",
    "name": "특허청 통지서 수신 리스트 (일일)",
    "category": "kipo_notice",
    "language": "ko",
    "trigger_keywords": ["통지서", "특허청", "KIPO"],
    "use_case": "매일 오전 특허청 수신 통지서 내역을 담당 변리사에게 발송",
    "variables": ["kipo_table_rows", "overseas_table_rows"],
    "subject_pattern": "({date}) 특허청 통지서수신 리스트",
}

# ──────────────────────────────────────────────

OUTBOUND_REMINDER_COST_EN = """\
Dear {recipient_name},

REMINDER: We would like to kindly follow up on our previous message below regarding the estimated costs and timeline for the above-referenced matter.

Could you please provide us with the requested information at your earliest convenience?

Your Ref.: {your_ref}
Our Ref.: {our_ref}
Matter: {matter_title}
Deadline: {deadline}

Please do not hesitate to contact us if you have any questions.

Best regards,

{sender_name}
{sender_title}
IP LAB Patent Law Firm (특허법인 아이피랩)
TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
"""
OUTBOUND_REMINDER_COST_EN_META = {
    "id": "outbound_reminder_cost_en",
    "name": "비용 견적 리마인더 (영문)",
    "category": "reminder",
    "language": "en",
    "trigger_keywords": ["Estimated Cost", "견적", "REMINDER", "Timeline"],
    "use_case": "외국 대리인에게 비용 견적 또는 타임라인 미회신 시 리마인더 발송",
    "variables": ["recipient_name", "your_ref", "our_ref", "matter_title", "deadline", "sender_name", "sender_title"],
    "subject_pattern": "REMINDER: [IP LAB] Request for Estimated Costs and Timeline / {your_ref}",
}

# ──────────────────────────────────────────────

OUTBOUND_OA_SUBMIT_COMPLETE_KO = """\
수신: {client_name}

안녕하세요. 특허법인 아이피랩의 {sender_name} {sender_title}입니다.

하기 국내 특허출원의 의견제출통지에 대응하는 의견서 및 명세서등보정서를 제출하였기에 보고 드립니다.

Our Ref.       {our_ref}
Your Ref.      {your_ref}
출원번호       {app_number}
출원일         {filing_date}
출원인         {applicant}
발명자         {inventors}
발명의 명칭    {title}
의견서 제출일  {submission_date}
기타사항       {notes}

본 건의 중간사건대응에 따른 청구서를 동봉하오니, 귀사의 절차에 따라 결제 확인 부탁드립니다.

*첨부서류: 의견서, 보정서, 관납료영수증, 청구서 – {attachment_count}부

본 건 및 기타 문의사항이 있으시면 언제든지 연락하여 주시기 바랍니다.

감사합니다.

{sender_name} {sender_title}
특허법인 아이피랩
TEL: 02-6925-{ext}
E-MAIL: {sender_email}
"""
OUTBOUND_OA_SUBMIT_COMPLETE_KO_META = {
    "id": "outbound_oa_submit_complete_ko",
    "name": "OA 대응 의견서/보정서 제출 완료보고 및 비용청구 (국문)",
    "category": "oa_complete",
    "language": "ko",
    "trigger_keywords": ["의견서", "보정서", "OA", "제출완료", "비용청구"],
    "use_case": "고객에게 OA(의견제출통지) 대응 완료 보고 및 청구서 발송",
    "variables": [
        "client_name", "sender_name", "sender_title", "our_ref", "your_ref",
        "app_number", "filing_date", "applicant", "inventors", "title",
        "submission_date", "notes", "attachment_count", "ext", "sender_email"
    ],
    "subject_pattern": "[아이피랩] {app_number}호 의견서/보정서 제출완료보고 및 비용청구의 건",
}

# ──────────────────────────────────────────────

OUTBOUND_FILING_COMPLETE_KO = """\
수신: {client_name}

안녕하세요. 특허법인 아이피랩의 {sender_name} {sender_title}입니다.

하기 특허출원을 완료하였기에 보고 드립니다.

Our Ref.    {our_ref}
Your Ref.   {your_ref}
출원번호    {app_number}
출원일      {filing_date}
출원인      {applicant}
발명자      {inventors}
발명의 명칭 {title}
국가        {country}
우선권 정보 {priority_info}

출원에 따른 청구서를 동봉하오니, 귀사의 절차에 따라 결제 확인 부탁드립니다.

*첨부서류: 출원서, 명세서, 도면, 관납료영수증, 청구서 – {attachment_count}부

감사합니다.

{sender_name} {sender_title}
특허법인 아이피랩
TEL: 02-6925-{ext}
E-MAIL: {sender_email}
"""
OUTBOUND_FILING_COMPLETE_KO_META = {
    "id": "outbound_filing_complete_ko",
    "name": "출원 완료 보고 및 비용청구 (국문)",
    "category": "filing_complete",
    "language": "ko",
    "use_case": "특허/실용신안 출원 완료 후 고객에게 보고 및 청구서 발송",
    "variables": [
        "client_name", "sender_name", "sender_title", "our_ref", "your_ref",
        "app_number", "filing_date", "applicant", "inventors", "title",
        "country", "priority_info", "attachment_count", "ext", "sender_email"
    ],
    "subject_pattern": "[아이피랩] {app_number}호 출원완료보고 및 비용청구의 건",
}

# ──────────────────────────────────────────────

OUTBOUND_DRAWING_REQUEST_KO = """\
안녕하세요. 특허법인 아이피랩의 {sender_name} {sender_title}입니다.

본 건에 대하여 {drawing_type} 도면 작업 의뢰 드립니다.

KR 작업 Ref.      {kr_ref}
Our Ref.          {our_ref}
발명의 명칭       {title}
실무담당자        {attorney_name} 변리사
실무담당자 E-mail {attorney_email}
실무담당자 직통번호 {attorney_tel}
번역완료 요청일   {due_date}
의뢰내용          {drawing_details}
우선권 출원정보   {priority_info}

감사합니다.
"""
OUTBOUND_DRAWING_REQUEST_KO_META = {
    "id": "outbound_drawing_request_ko",
    "name": "도면 작업 의뢰 (국문)",
    "category": "drawing_request",
    "language": "ko",
    "trigger_keywords": ["도면", "도면의뢰"],
    "use_case": "외부 도면 업체에 특허 도면 작업 의뢰 발송",
    "variables": [
        "sender_name", "sender_title", "drawing_type", "kr_ref", "our_ref",
        "title", "attorney_name", "attorney_email", "attorney_tel",
        "due_date", "drawing_details", "priority_info"
    ],
    "subject_pattern": "[도면의뢰][아이피랩][{our_ref}] {drawing_type} 도면 의뢰",
}

# ──────────────────────────────────────────────

OUTBOUND_NEW_CASE_INTERNAL_KO = """\
[사건수임]

신규사건을 수임하였습니다.

하기 담당자는 본 건을 확인해 주시기 바랍니다.

YourRef  | OurRef    | 의뢰인   | 접수일      | 사건마감일   | 담당자 | 현재상태                    | 명칭       | 비고
{your_ref} | {our_ref} | {client} | {recv_date} | {deadline} | {assignee} | {status} | {title} | {notes}

[관리번호: {mgmt_no} / 대표발명자: {main_inventor}]
[발명공개여부] {is_public}
[공동출원] {is_joint}
[연구과제] {is_research}
담당변리사: {attorney}
"""
OUTBOUND_NEW_CASE_INTERNAL_KO_META = {
    "id": "outbound_new_case_internal_ko",
    "name": "신규 사건수임 내부 알림 (국문)",
    "category": "new_case",
    "language": "ko",
    "trigger_keywords": ["사건수임", "신규수임"],
    "use_case": "내부 직원에게 신규 사건 수임 알림 발송",
    "variables": [
        "your_ref", "our_ref", "client", "recv_date", "deadline",
        "assignee", "status", "title", "notes", "mgmt_no",
        "main_inventor", "is_public", "is_joint", "is_research", "attorney"
    ],
    "subject_pattern": "[사건수임] {recv_date}({client})",
}

# ──────────────────────────────────────────────

OUTBOUND_GPOA_INSTRUCTION_EN = """\
Dear {recipient_name},

Thank you for your e-mail below.

{numbered_responses}

Please let us know if you have any further questions.

Best regards,

{sender_name} ({gender_title})
{sender_title}

on behalf of

{partner_name} ({partner_gender_title})
{partner_title}

IP LAB Patent Law Firm (특허법인 아이피랩)
5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea
TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
WEBSITE: https://en.ip-lab.co.kr/
"""
OUTBOUND_GPOA_INSTRUCTION_EN_META = {
    "id": "outbound_gpoa_instruction_en",
    "name": "GPOA/위임장 관련 영문 안내 회신",
    "category": "gpoa",
    "language": "en",
    "trigger_keywords": ["GPOA", "Power of Attorney", "POA", "representation"],
    "use_case": "외국 대리인의 GPOA 또는 위임 관련 문의에 대한 구체적인 답변 발송",
    "variables": [
        "recipient_name", "numbered_responses", "sender_name", "gender_title",
        "sender_title", "partner_name", "partner_gender_title", "partner_title"
    ],
}

# ──────────────────────────────────────────────
# INBOUND 유형별 → 권장 회신 초안
# ──────────────────────────────────────────────

INBOUND_OA_REQUEST = {
    "id": "inbound_oa_request",
    "name": "OA 대응안 작성 요청 (수신)",
    "category": "oa_related",
    "trigger_keywords": ["OA 대응", "거절이유", "Office Action", "의견제출통지"],
    "description": "고객(대학/기업)으로부터 OA 대응안 작성 요청을 받은 경우",
    "reply_template_id": "outbound_oa_submit_complete_ko",
    "reply_guide": (
        "1. 사건번호(Our Ref)와 출원번호 확인\n"
        "2. 거절이유 내용 파악 후 대응 전략 검토\n"
        "3. OA 마감일 캘린더 등록\n"
        "4. 완료 후 outbound_oa_submit_complete_ko 템플릿으로 보고"
    ),
    "auto_reply_ko": (
        "안녕하세요.\n\n"
        "해당 건 OA 대응안 작성 요청 잘 수신하였습니다.\n"
        "내용을 검토 후 {deadline}까지 초안을 전달 드리겠습니다.\n\n"
        "감사합니다."
    ),
}

INBOUND_FILING_ORDER = {
    "id": "inbound_filing_order",
    "name": "출원 의뢰 수신",
    "category": "filing_order",
    "trigger_keywords": ["출원의뢰", "출원 요청", "filing order", "New Application"],
    "description": "고객 또는 외국 대리인으로부터 신규 출원 지시를 받은 경우",
    "reply_template_id": "outbound_filing_complete_ko",
    "reply_guide": (
        "1. 출원 정보(발명자, 출원인, 우선권) 확인\n"
        "2. 마감일(우선권 기한) 확인 및 캘린더 등록\n"
        "3. 출원 완료 후 outbound_filing_complete_ko 로 보고"
    ),
    "auto_reply_en": (
        "Dear Sir/Madam:\n\n"
        "We acknowledge receipt of your filing instructions for the above-referenced matter.\n"
        "We will proceed accordingly and keep you informed.\n\n"
        "Best regards,\n{sender_name}\nIP LAB Patent Law Firm"
    ),
}

INBOUND_RENEWAL_REMINDER = {
    "id": "inbound_renewal_reminder",
    "name": "연차료/갱신료 알림 수신",
    "category": "fee_related",
    "trigger_keywords": ["Renewal Fee", "Annuity", "TAX", "연차료", "갱신료"],
    "description": "외국 대리인으로부터 연차료·갱신료 납부 알림을 받은 경우",
    "reply_template_id": "outbound_acknowledge_en",
    "reply_guide": (
        "1. 납부 지시 여부 확인 (고객 승인 필요시 고객에게 먼저 문의)\n"
        "2. 납부 지시 시 outbound_acknowledge_en 으로 수신 확인 회신\n"
        "3. 납부 완료 후 영수증 보관"
    ),
}

INBOUND_DRAFT_REVIEW = {
    "id": "inbound_draft_review",
    "name": "외국 대리인 초안 수신 (검토 요청)",
    "category": "document_request",
    "trigger_keywords": ["Draft", "초안", "specification", "명세서"],
    "description": "외국 대리인으로부터 출원 명세서 또는 의견서 초안을 받아 검토해야 하는 경우",
    "reply_guide": (
        "1. 초안 내용 검토\n"
        "2. 수정 의견 또는 승인 회신\n"
        "3. 마감일(Due Date) 캘린더 등록"
    ),
    "auto_reply_en": (
        "Dear {sender_name},\n\n"
        "Thank you for sending the draft for the above-referenced matter.\n"
        "We will review the draft and provide our comments by {review_deadline}.\n\n"
        "Best regards,\n{our_name}\nIP LAB Patent Law Firm"
    ),
}

INBOUND_COST_ESTIMATE_REQUEST = {
    "id": "inbound_cost_estimate_request",
    "name": "비용 견적 요청 수신",
    "category": "fee_related",
    "trigger_keywords": ["Estimated Cost", "견적", "비용 문의", "Timeline"],
    "description": "외국 대리인 또는 고객으로부터 비용 견적 요청을 받은 경우",
    "reply_guide": (
        "1. 해당 국가/사건 유형의 관납료·대리인 비용 산출\n"
        "2. 견적서 작성 후 회신 (미처리 시 outbound_reminder_cost_en 활용)"
    ),
    "auto_reply_en": (
        "Dear {sender_name},\n\n"
        "Thank you for your inquiry regarding costs for the above matter.\n"
        "We are currently preparing the cost estimate and will revert to you shortly.\n\n"
        "Best regards,\n{our_name}\nIP LAB Patent Law Firm"
    ),
}

INBOUND_DRAWING_ORDER = {
    "id": "inbound_drawing_order",
    "name": "도면 작업 의뢰 수신 (도면업체 → 아이피랩)",
    "category": "document_request",
    "trigger_keywords": ["도면의뢰", "도면 작업"],
    "description": "내부에서 도면 의뢰가 들어온 경우 (실제로는 outbound로 외부에 전달)",
    "reply_guide": (
        "1. 도면 명세 확인 (마감일, Ref, 의뢰 내용)\n"
        "2. 도면 업체에 outbound_drawing_request_ko 발송"
    ),
}

# ──────────────────────────────────────────────
# 출원의뢰 템플릿 (OUTBOUND)
# ──────────────────────────────────────────────

OUTBOUND_FILING_INSTRUCTION_EN = """\
Dear {recipient_name},

We hope this message finds you well.

We would like to instruct you to file a new patent application based on the following information.

[Filing Information]
Your Ref.        : {your_ref}
Our Ref.         : {our_ref}
Title            : {title}
Applicant(s)     : {applicants}
Inventor(s)      : {inventors}
Priority         : {priority_app_no} ({priority_date})
Deadline         : {deadline}
Country/Region   : {country}
Special Notes    : {notes}

Please find the relevant documents attached hereto.

Kindly acknowledge receipt of this e-mail and confirm that you will proceed with the filing accordingly.

Should you have any questions or require additional information, please do not hesitate to contact us.

Best regards,

{sender_name} ({gender_title}) / {sender_title}

on behalf of

{partner_name} ({partner_gender}) / {partner_title}

IP LAB Patent Law Firm (특허법인 아이피랩)
5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea
TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
WEBSITE: https://en.ip-lab.co.kr/
"""
OUTBOUND_FILING_INSTRUCTION_EN_META = {
    "id": "outbound_filing_instruction_en",
    "name": "출원 지시 발신 (영문, 외국 대리인)",
    "category": "filing_instruction",
    "language": "en",
    "trigger_keywords": ["Filing Instructions", "Please file", "filing order", "출원지시"],
    "use_case": "외국 대리인(일본·중국·EP·미국 등)에게 신규 출원 지시 발송",
    "variables": [
        "recipient_name", "your_ref", "our_ref", "title", "applicants", "inventors",
        "priority_app_no", "priority_date", "deadline", "country", "notes",
        "sender_name", "gender_title", "sender_title",
        "partner_name", "partner_gender", "partner_title"
    ],
    "subject_pattern": "[IP LAB] Filing Instructions (Due_{deadline}) / {our_ref}",
}

# ──────────────────────────────────────────────

OUTBOUND_FILING_INSTRUCTION_KO = """\
안녕하세요, {recipient_name}님.

특허법인 아이피랩 {sender_dept} {sender_name} {sender_title}입니다.

하기 건에 대한 출원을 진행 부탁드립니다.

[출원 의뢰 사항]
Our Ref.     : {our_ref}
Your Ref.    : {your_ref}
발명의 명칭  : {title}
출원인       : {applicants}
발명자       : {inventors}
우선권 정보  : {priority_app_no} ({priority_date})
출원 마감일  : {deadline}
국가         : {country}
특이사항     : {notes}

관련 서류를 첨부하오니 확인 후 진행 부탁드립니다.
진행 시 수신 확인 회신 부탁드립니다.

추가로 필요한 사항이 있으시면 언제든지 연락 부탁드립니다.

감사합니다.

{sender_name} {sender_title}
특허법인 아이피랩 {sender_dept}
TEL: 02-6925-{ext} | E-MAIL: {sender_email}
"""
OUTBOUND_FILING_INSTRUCTION_KO_META = {
    "id": "outbound_filing_instruction_ko",
    "name": "출원 지시 발신 (국문, 국내외 대리인)",
    "category": "filing_instruction",
    "language": "ko",
    "trigger_keywords": ["출원의뢰", "출원 의뢰", "출원 지시", "출원을 진행"],
    "use_case": "국내 또는 국문 커뮤니케이션하는 외국 대리인에게 출원 지시 발송",
    "variables": [
        "recipient_name", "sender_dept", "sender_name", "sender_title",
        "our_ref", "your_ref", "title", "applicants", "inventors",
        "priority_app_no", "priority_date", "deadline", "country", "notes",
        "ext", "sender_email"
    ],
    "subject_pattern": "[IP LAB] 출원의뢰 (Due_{deadline}) / {our_ref}",
}

# ──────────────────────────────────────────────
# 리비전의뢰 템플릿 (OUTBOUND)
# ──────────────────────────────────────────────

OUTBOUND_REVISION_DRAWINGS_EN = """\
Dear {recipient_name},

We hope this message finds you well.

Further to our previous correspondence regarding the above-referenced matter, we would like to inform you that the drawings for this case have now been completed.

Please find the drawings attached hereto. We kindly ask that you proceed with the revision, taking the attached files into consideration.

[Case Information]
Your Ref. : {your_ref}
Our Ref.  : {our_ref}
Title     : {title}
Deadline  : {deadline}

Should you have any questions or require further information, please do not hesitate to contact us.

Thank you for your continued cooperation. Please acknowledge safe receipt of this email by return.

Best regards,

{sender_name} ({gender_title}) / {sender_title}

on behalf of

{partner_name} ({partner_gender}) / {partner_title}

IP LAB Patent Law Firm (특허법인 아이피랩)
5th Floor, MARCUS, 55, Magokdong-ro, Gangseo-gu, Seoul, 07802, Republic of Korea
TEL: +82-2-6925-4821 | FAX: +82-2-6925-4825
WEBSITE: https://en.ip-lab.co.kr/
"""
OUTBOUND_REVISION_DRAWINGS_EN_META = {
    "id": "outbound_revision_drawings_en",
    "name": "도면 리비전 발송 (영문, 외국 대리인)",
    "category": "revision",
    "language": "en",
    "trigger_keywords": ["Revision", "Drawings for Revision", "도면 리비전", "drawing revision"],
    "use_case": "도면 작업 완료 후 외국 대리인에게 리비전(수정 반영) 요청과 함께 발송",
    "variables": [
        "recipient_name", "your_ref", "our_ref", "title", "deadline",
        "sender_name", "gender_title", "sender_title",
        "partner_name", "partner_gender", "partner_title"
    ],
    "subject_pattern": "[IP LAB] Sending Drawings for Revision / {our_ref}",
}

# ──────────────────────────────────────────────

OUTBOUND_REVISION_SPEC_KO = """\
{recipient_name}님께,

안녕하세요, {sender_name} {sender_title}입니다.

보내주신 {doc_type} 확인했습니다. 작업해 주셔서 감사합니다.

{doc_type}에 관해 수정 요청사항이 있어서 안내드립니다.

[수정 요청 사항]
{revision_items}

자세한 사항은 첨부 파일에 표기하였으니 확인 부탁드립니다.
문의/요청사항이 있으시면 언제든지 연락 주시기 바랍니다.

Our Ref.    : {our_ref}
수정 마감일 : {deadline}

감사합니다.

{sender_name} {sender_title}
특허법인 아이피랩
TEL: 02-6925-{ext} | E-MAIL: {sender_email}
"""
OUTBOUND_REVISION_SPEC_KO_META = {
    "id": "outbound_revision_spec_ko",
    "name": "명세서/도면 수정 요청 (국문)",
    "category": "revision",
    "language": "ko",
    "trigger_keywords": ["수정 요청", "리비전", "revision", "수정사항", "명세서 수정", "도면 수정"],
    "use_case": "도면업체·번역사 등에게 명세서 또는 도면 수정 사항을 구체적으로 전달",
    "variables": [
        "recipient_name", "sender_name", "sender_title", "doc_type",
        "revision_items", "our_ref", "deadline", "ext", "sender_email"
    ],
    "subject_pattern": "RE: [{our_ref}] {doc_type} 수정 요청",
    "notes": (
        "revision_items는 번호 매긴 리스트로 작성:\n"
        "1. 도 9A: ...\n2. 도 1: ...\n3. ..."
    ),
}

# ──────────────────────────────────────────────
# 출원의뢰·리비전 수신 유형
# ──────────────────────────────────────────────

INBOUND_FILING_INSTRUCTION_FROM_CLIENT = {
    "id": "inbound_filing_instruction_from_client",
    "name": "고객의 출원의뢰 수신 (국내)",
    "category": "filing_order",
    "trigger_keywords": ["출원의뢰", "출원 의뢰", "출원 요청", "출원해 주", "출원 부탁"],
    "description": "국내 고객(기업·대학)이 아이피랩에 직접 특허 출원을 의뢰한 경우",
    "reply_guide": (
        "1. 발명신고서·명세서 초안 접수 여부 확인\n"
        "2. Our Ref(사건번호) 부여 및 담당 변리사 지정\n"
        "3. 출원 마감일(우선권·PCT 기한) 캘린더 등록\n"
        "4. 접수 확인 회신 발송\n"
        "5. 출원 완료 후 outbound_filing_complete_ko 로 보고"
    ),
    "auto_reply_ko": (
        "안녕하세요.\n\n"
        "출원 의뢰 잘 수신하였습니다.\n"
        "검토 후 진행 일정 및 담당자를 안내드리겠습니다.\n\n"
        "감사합니다."
    ),
}

INBOUND_FILING_INSTRUCTION_FROM_FOREIGN = {
    "id": "inbound_filing_instruction_from_foreign",
    "name": "외국 대리인의 출원의뢰 수신 (영문)",
    "category": "filing_order",
    "trigger_keywords": [
        "filing order", "filing instruction", "Please file", "Please proceed with filing",
        "New Application", "national phase", "PCT entry"
    ],
    "description": "외국 대리인(미국·일본·중국·EP 등)으로부터 한국 출원 또는 PCT 국내단계 진입 지시를 받은 경우",
    "reply_guide": (
        "1. Your Ref / Our Ref / Due Date 확인\n"
        "2. 우선권 서류·번역문 첨부 여부 확인\n"
        "3. 마감일 캘린더 등록\n"
        "4. outbound_acknowledge_en 으로 수신 확인 회신\n"
        "5. 출원 완료 후 영문 완료보고 발송"
    ),
    "auto_reply_en": (
        "Dear Sir/Madam:\n\n"
        "We acknowledge receipt of your filing instructions for the above-referenced matter.\n"
        "We will proceed accordingly and revert to you with the filing details upon completion.\n\n"
        "Best regards,\n{sender_name}\nIP LAB Patent Law Firm"
    ),
}

INBOUND_REVISION_FROM_FOREIGN = {
    "id": "inbound_revision_from_foreign",
    "name": "외국 대리인의 리비전 요청 수신 (영문)",
    "category": "revision",
    "trigger_keywords": [
        "revision", "revise", "Application Revisions", "redlined", "amendment",
        "Formals for Signature", "suggested revisions"
    ],
    "description": "외국 대리인으로부터 명세서·도면·클레임 수정안(redline)을 받아 검토·반영이 필요한 경우",
    "reply_guide": (
        "1. 수정안(redline) 및 메모 확인\n"
        "2. 마감일(bar date / filing deadline) 확인 및 캘린더 등록\n"
        "3. 수정 사항 검토 후 승인 또는 역제안 회신\n"
        "4. 최종 확정 후 outbound_revision_drawings_en 또는 수정 명세서 발송"
    ),
    "auto_reply_en": (
        "Dear {sender_name},\n\n"
        "Thank you for sending the revised application and accompanying memo for the above-referenced matter.\n"
        "We will review the proposed revisions and revert to you with our comments by {review_deadline}.\n\n"
        "Best regards,\n{our_name}\nIP LAB Patent Law Firm"
    ),
}

INBOUND_REVISION_FROM_INTERNAL = {
    "id": "inbound_revision_from_internal",
    "name": "내부 변리사의 수정 요청 수신 (국문)",
    "category": "revision",
    "trigger_keywords": ["수정 요청", "수정사항", "수정해 주", "보완 요청", "명세서 수정", "도면 수정"],
    "description": "내부 변리사 또는 담당자로부터 도면·명세서 수정 지시를 받은 경우",
    "reply_guide": (
        "1. 수정 항목 목록 확인 (번호 매긴 리스트)\n"
        "2. 수정 마감일 확인\n"
        "3. 수정 완료 후 outbound_revision_spec_ko 발송"
    ),
    "auto_reply_ko": (
        "{sender_name}님께,\n\n"
        "수정 요청 잘 수신하였습니다.\n"
        "확인 후 {deadline}까지 수정본을 전달드리겠습니다.\n\n"
        "감사합니다."
    ),
}

# ──────────────────────────────────────────────
# 템플릿 레지스트리
# ──────────────────────────────────────────────

OUTBOUND_TEMPLATES = [
    (OUTBOUND_ACKNOWLEDGE_EN, OUTBOUND_ACKNOWLEDGE_EN_META),
    (OUTBOUND_ACKNOWLEDGE_KO, OUTBOUND_ACKNOWLEDGE_KO_META),
    (OUTBOUND_KIPO_NOTICE_LIST, OUTBOUND_KIPO_NOTICE_LIST_META),
    (OUTBOUND_REMINDER_COST_EN, OUTBOUND_REMINDER_COST_EN_META),
    (OUTBOUND_OA_SUBMIT_COMPLETE_KO, OUTBOUND_OA_SUBMIT_COMPLETE_KO_META),
    (OUTBOUND_FILING_COMPLETE_KO, OUTBOUND_FILING_COMPLETE_KO_META),
    (OUTBOUND_FILING_INSTRUCTION_EN, OUTBOUND_FILING_INSTRUCTION_EN_META),
    (OUTBOUND_FILING_INSTRUCTION_KO, OUTBOUND_FILING_INSTRUCTION_KO_META),
    (OUTBOUND_REVISION_DRAWINGS_EN, OUTBOUND_REVISION_DRAWINGS_EN_META),
    (OUTBOUND_REVISION_SPEC_KO, OUTBOUND_REVISION_SPEC_KO_META),
    (OUTBOUND_DRAWING_REQUEST_KO, OUTBOUND_DRAWING_REQUEST_KO_META),
    (OUTBOUND_NEW_CASE_INTERNAL_KO, OUTBOUND_NEW_CASE_INTERNAL_KO_META),
    (OUTBOUND_GPOA_INSTRUCTION_EN, OUTBOUND_GPOA_INSTRUCTION_EN_META),
]

INBOUND_TYPES = [
    INBOUND_OA_REQUEST,
    INBOUND_FILING_ORDER,
    INBOUND_FILING_INSTRUCTION_FROM_CLIENT,
    INBOUND_FILING_INSTRUCTION_FROM_FOREIGN,
    INBOUND_RENEWAL_REMINDER,
    INBOUND_DRAFT_REVIEW,
    INBOUND_REVISION_FROM_FOREIGN,
    INBOUND_REVISION_FROM_INTERNAL,
    INBOUND_COST_ESTIMATE_REQUEST,
    INBOUND_DRAWING_ORDER,
]

OUTBOUND_BY_ID = {meta["id"]: (body, meta) for body, meta in OUTBOUND_TEMPLATES}
INBOUND_BY_ID = {t["id"]: t for t in INBOUND_TYPES}


def get_template_for_mail(subject: str, body: str, direction: str) -> dict | None:
    """
    메일 제목/본문에서 가장 적합한 템플릿을 반환.
    direction: 'outbound' 또는 'inbound'
    """
    text = (subject + " " + body).lower()

    if direction == "outbound":
        for body_tpl, meta in OUTBOUND_TEMPLATES:
            keywords = meta.get("trigger_keywords", [])
            if any(kw.lower() in text for kw in keywords):
                return {"body": body_tpl, **meta}
    else:
        for t in INBOUND_TYPES:
            keywords = t.get("trigger_keywords", [])
            if any(kw.lower() in text for kw in keywords):
                return t

    return None
