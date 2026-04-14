"""Expand Case model with Excel fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-14

0001에 있는 컬럼: id, case_number, app_number, reg_number, client_name,
                  client_domain, country, case_type, status, deadline,
                  attorney_id, staff_id, created_at
이 마이그레이션에서 추가하는 컬럼만 포함 (중복 제외)
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_COLS = [
    # 참조번호
    ("your_ref",           sa.String(100)),
    ("intl_app_number",    sa.String(100)),
    # 명칭
    ("title_ko",           sa.Text()),
    ("title_en",           sa.Text()),
    # 고객
    ("applicant",          sa.String(200)),
    ("applicant_contact",  sa.String(100)),
    # 분류
    ("division",           sa.String(10)),
    ("app_category",       sa.String(50)),
    ("app_kind",           sa.String(50)),
    # 담당 (문자열 — 기존 attorney_id/staff_id UUID 컬럼은 유지, 모델에선 무시)
    ("attorney",           sa.String(50)),
    ("department",         sa.String(50)),
    # 마감일
    ("app_deadline",       sa.Date()),
    ("reg_deadline",       sa.Date()),
    ("annual_deadline",    sa.Date()),
    # 날짜
    ("filed_at",           sa.Date()),
    ("registered_at",      sa.Date()),
    ("received_at",        sa.Date()),
    # 기타
    ("ipc",                sa.String(100)),
    ("notes",              sa.Text()),
]


def upgrade() -> None:
    for col_name, col_type in NEW_COLS:
        op.add_column("cases", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    for col_name, _ in reversed(NEW_COLS):
        op.drop_column("cases", col_name)
