"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cases
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("case_number", sa.String(50), nullable=False),
        sa.Column("app_number", sa.String(50), nullable=True),
        sa.Column("reg_number", sa.String(50), nullable=True),
        sa.Column("client_name", sa.String(200), nullable=False),
        sa.Column("client_domain", sa.String(100), nullable=True),
        sa.Column("country", sa.String(10), nullable=False),
        sa.Column("case_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("attorney_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number"),
    )
    op.create_index("idx_cases_case_number", "cases", ["case_number"])
    op.create_index("idx_cases_client_domain", "cases", ["client_domain"])

    # parties
    op.create_table(
        "parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("org_name", sa.String(200), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_parties_email", "parties", ["email"])

    # mail_messages
    op.create_table(
        "mail_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("graph_message_id", sa.String(500), nullable=False),
        sa.Column("internet_message_id", sa.String(500), nullable=True),
        sa.Column("conversation_id", sa.String(500), nullable=True),
        sa.Column("from_email", sa.String(200), nullable=True),
        sa.Column("from_name", sa.String(200), nullable=True),
        sa.Column("to_emails", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cc_emails", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("has_attachments", sa.Boolean(), nullable=False, default=False),
        sa.Column("detected_language", sa.String(10), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requires_reply", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.String(10), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_translation", sa.Text(), nullable=True),
        sa.Column("ai_classification", sa.String(50), nullable=True),
        sa.Column("processing_status", sa.String(30), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("graph_message_id"),
    )
    op.create_index("idx_mail_messages_case_id", "mail_messages", ["case_id"])
    op.create_index("idx_mail_messages_received_at", "mail_messages", ["received_at"])
    op.create_index("idx_mail_messages_conversation", "mail_messages", ["conversation_id"])

    # mail_attachments
    op.create_table(
        "mail_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("mail_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("graph_attachment_id", sa.String(500), nullable=True),
        sa.Column("filename", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("stored_path", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["mail_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # draft_responses
    op.create_table(
        "draft_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("source_mail_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generated_body_ko", sa.Text(), nullable=True),
        sa.Column("generated_body_en", sa.Text(), nullable=True),
        sa.Column("reviewer_body", sa.Text(), nullable=True),
        sa.Column("suggested_to", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggested_cc", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approval_status", sa.String(30), nullable=False, default="pending"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graph_sent_message_id", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_mail_id"], ["mail_messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("draft_responses")
    op.drop_table("mail_attachments")
    op.drop_table("mail_messages")
    op.drop_table("parties")
    op.drop_table("cases")
