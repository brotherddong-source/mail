"""Expand Case model with Excel fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-14

0001에 있는 컬럼: id, case_number, app_number, reg_number, client_name,
                  client_domain, country, case_type, status, deadline,
                  attorney_id, staff_id, created_at
이 마이그레이션에서 추가하는 컬럼만 포함 (중복 제외)
IF NOT EXISTS 사용 → 이미 존재해도 오류 없이 통과
"""
from typing import Sequence, Union
from alembic import op
from sqlalchemy import text

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (컬럼명, PostgreSQL 타입)
NEW_COLS = [
    ("your_ref",          "varchar(100)"),
    ("intl_app_number",   "varchar(100)"),
    ("title_ko",          "text"),
    ("title_en",          "text"),
    ("applicant",         "varchar(200)"),
    ("applicant_contact", "varchar(100)"),
    ("division",          "varchar(10)"),
    ("app_category",      "varchar(50)"),
    ("app_kind",          "varchar(50)"),
    ("attorney",          "varchar(50)"),
    ("department",        "varchar(50)"),
    ("app_deadline",      "date"),
    ("reg_deadline",      "date"),
    ("annual_deadline",   "date"),
    ("filed_at",          "date"),
    ("registered_at",     "date"),
    ("received_at",       "date"),
    ("ipc",               "varchar(100)"),
    ("notes",             "text"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for col_name, col_type in NEW_COLS:
        # PostgreSQL ALTER TABLE ... ADD COLUMN IF NOT EXISTS (9.6+)
        conn.execute(
            text(f"ALTER TABLE cases ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        )


def downgrade() -> None:
    conn = op.get_bind()
    for col_name, _ in reversed(NEW_COLS):
        conn.execute(
            text(f"ALTER TABLE cases DROP COLUMN IF EXISTS {col_name}")
        )
