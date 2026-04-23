"""Add patent-specific date fields to cases

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-23
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    cols = [
        "priority_date               DATE",
        "public_notice_exception_date DATE",
        "exam_request_date           DATE",
        "exam_request_deadline       DATE",
        "published_at                DATE",
        "intl_filed_at               DATE",
        "national_phase_at           DATE",
    ]
    for col in cols:
        op.execute(f"ALTER TABLE cases ADD COLUMN IF NOT EXISTS {col}")


def downgrade() -> None:
    for col in [
        "priority_date", "public_notice_exception_date",
        "exam_request_date", "exam_request_deadline",
        "published_at", "intl_filed_at", "national_phase_at",
    ]:
        op.execute(f"ALTER TABLE cases DROP COLUMN IF EXISTS {col}")
