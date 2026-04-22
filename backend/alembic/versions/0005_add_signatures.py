"""Add signatures table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS signatures (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sender_email VARCHAR(200) NOT NULL,
            label       VARCHAR(200) NOT NULL,
            language    VARCHAR(5)   NOT NULL DEFAULT 'ko',
            body        TEXT         NOT NULL,
            is_default  BOOLEAN      NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_signatures_sender ON signatures(sender_email)")

    # inline 이미지/첨부 지원을 위해 mail_attachments에 컬럼 추가
    op.execute("ALTER TABLE mail_attachments ADD COLUMN IF NOT EXISTS content_id  TEXT")
    op.execute("ALTER TABLE mail_attachments ADD COLUMN IF NOT EXISTS is_inline   BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE mail_attachments ADD COLUMN IF NOT EXISTS content_b64 TEXT")  # base64 data


def downgrade() -> None:
    op.drop_table("signatures")
