"""
직원 초기 데이터 시드
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.users.models import User

STAFF = [
    # (이름, 이메일, 부서, 관리자여부)
    ("김동일", "dikim@ip-lab.co.kr", None, True),       # 대표 → 관리자
    ("김미령", "mrkim@ip-lab.co.kr", "특허3부", False),
    ("박민수", "mspark@ip-lab.co.kr", "특허1부", False),
    ("우재형", "jhwoo@ip-lab.co.kr", "특허2부", False),
    ("신지원", "jwshin@ip-lab.co.kr", "특허1부", False),
    ("이동영", "dylee@ip-lab.co.kr", "특허2부", False),
    ("이민식", "mslee@ip-lab.co.kr", "특허3부", False),
    ("조운영", "wycho@ip-lab.co.kr", "특허3부", False),
    ("황윤지", "yjhwang@ip-lab.co.kr", "특허3부", False),
    ("김도희", "dhkim@ip-lab.co.kr", "특허2부", False),
    ("김유진", "ujkim@ip-lab.co.kr", "특허3부", False),
    ("오세현", "shoh@ip-lab.co.kr", "특허3부", False),
    ("유재호", "jhyou@ip-lab.co.kr", "특허1부", False),
    ("장소현", "shjang@ip-lab.co.kr", "특허3부", False),
    ("김주윤", "jykim@ip-lab.co.kr", "특허1부", False),
    ("김준표", "jpkim@ip-lab.co.kr", "특허3부", False),
    ("배상혁", "shbae@ip-lab.co.kr", "특허3부", False),
    ("이민우", "mwlee@ip-lab.co.kr", "특허3부", False),
    ("이성재", "sjlee@ip-lab.co.kr", "특허1부", False),
    ("이주연", "jylee@ip-lab.co.kr", "특허1부", False),
    ("장솔", "sjang@ip-lab.co.kr", "특허1부", False),
    ("정채현", "chjeong@ip-lab.co.kr", "특허2부", False),
    ("조윤아", "yacho@ip-lab.co.kr", "특허2부", False),
    ("최수연", "sychoi@ip-lab.co.kr", "특허3부", False),
    ("황광옥", "kohwang@ip-lab.co.kr", "국내관리", False),
    ("나해지", "hjna@ip-lab.co.kr", "국내관리", False),
    ("김민지", "mjkim@ip-lab.co.kr", "국내관리", False),
    ("이정은", "jelee@ip-lab.co.kr", "해외관리", False),
    ("이가은", "gekim@ip-lab.co.kr", "해외관리", False),
]

SHARED_MAILBOXES = [
    "ip@ip-lab.co.kr",
    "mail@ip-lab.co.kr",
]


async def seed_users(db: AsyncSession) -> None:
    """직원 목록이 없을 때만 시드 실행"""
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        return  # 이미 시드됨

    for name, email, dept, is_admin in STAFF:
        db.add(User(
            name=name,
            email=email,
            department=dept,
            is_active=True,
            is_admin=is_admin,
        ))

    await db.commit()
