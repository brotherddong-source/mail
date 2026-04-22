"""Add mail extraction fields: exam_request, priority, foreign_agent_refs

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-22

메일 자동 파싱으로 채울 수 있는 필드 추가.
  - cases.exam_requested    : 심사청구 여부 (Y/N/null)
  - cases.overseas_deadline : 해외출원마감일 (국내 출원완료보고에 명시됨)
  - cases.priority_info     : 우선권 정보 JSONB [{app_no, country, date}]
  - cases.foreign_agent_refs: 국가별 외국 대리인 Ref JSONB [{country, agent, their_ref}]
  - parties.is_inventor     : 발명자 여부 bool (role='inventor' 보완)

IF NOT EXISTS → 이미 존재해도 오류 없이 통과
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CASES_COLS = [
    # 심사청구 여부: 출원완료보고 메일에서 "심사청구여부 Y/N" 추출
    ("exam_requested",     "varchar(1)"),        # 'Y' / 'N'

    # 해외출원마감일: 국내 출원완료보고에 별도 명시 (reg_deadline과 구분)
    ("overseas_deadline",  "date"),

    # 우선권 정보: [{app_no: "10-2025-XXXXXXX", country: "KR", date: "2025-05-26"}]
    # 출원의뢰(영문) / 리비전 메일에서 "Priority: KR ... (May 26, 2025)" 추출
    ("priority_info",      "jsonb"),

    # 국가별 외국 대리인 Ref: [{country:"JP", agent:"ITOH", their_ref:"JLABP2607"}]
    # Your Ref가 대리인마다 달라 단일 your_ref 컬럼으로 부족
    ("foreign_agent_refs", "jsonb"),
]

PARTIES_COLS = [
    # 발명자 전용 플래그 (role='inventor'를 bool로도 관리해 쿼리 편의성 향상)
    ("is_inventor", "boolean default false"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for col_name, col_type in CASES_COLS:
        conn.execute(
            text(f"ALTER TABLE cases ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        )
    for col_name, col_type in PARTIES_COLS:
        conn.execute(
            text(f"ALTER TABLE parties ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        )


def downgrade() -> None:
    conn = op.get_bind()
    for col_name, _ in reversed(PARTIES_COLS):
        conn.execute(text(f"ALTER TABLE parties DROP COLUMN IF EXISTS {col_name}"))
    for col_name, _ in reversed(CASES_COLS):
        conn.execute(text(f"ALTER TABLE cases DROP COLUMN IF EXISTS {col_name}"))
