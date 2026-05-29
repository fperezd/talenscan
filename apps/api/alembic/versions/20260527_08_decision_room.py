"""extend client_shortlists into decision room + events table

Revision ID: 20260527_08
Revises: 20260527_07
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260527_08"
down_revision = "20260527_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- client_shortlists: Decision Room enrichment ------------------------
    op.add_column(
        "client_shortlists",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("client_contact_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("client_contact_email", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("client_contact_company", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("access_code_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("access_code_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    # access_code_required = False por default mantiene comportamiento histórico:
    # los shortlists pre-existentes siguen funcionando sin gate.
    op.add_column(
        "client_shortlists",
        sa.Column(
            "access_code_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("last_invitation_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("intro_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "show_availability",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "show_salary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "show_risks",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "show_comparison",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "allow_comments",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "allow_rating",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column(
            "allow_report_download",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlists",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- client_shortlist_items: consultant overrides -----------------------
    op.add_column(
        "client_shortlist_items",
        sa.Column(
            "is_pinned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("recommendation", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("consultant_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column(
            "why_fits",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column(
            "risks_or_validations",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("evidence_level", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("availability", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("salary_expectation", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column(
            "salary_share_authorized",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "client_shortlist_items",
        sa.Column("rating", sa.SmallInteger(), nullable=True),
    )

    # --- decision_room_events ------------------------------------------------
    op.create_table(
        "decision_room_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "shortlist_id",
            sa.Integer(),
            sa.ForeignKey("client_shortlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("client_shortlist_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("event_label", sa.String(length=200), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("actor_name", sa.String(length=200), nullable=True),
        sa.Column("actor_email", sa.String(length=200), nullable=True),
        sa.Column(
            "event_metadata",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_decision_room_events_shortlist_id",
        "decision_room_events",
        ["shortlist_id"],
    )
    op.create_index(
        "ix_decision_room_events_created_at",
        "decision_room_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_decision_room_events_created_at", table_name="decision_room_events"
    )
    op.drop_index(
        "ix_decision_room_events_shortlist_id", table_name="decision_room_events"
    )
    op.drop_table("decision_room_events")

    for column in (
        "rating",
        "salary_share_authorized",
        "salary_expectation",
        "availability",
        "evidence_level",
        "risks_or_validations",
        "why_fits",
        "consultant_summary",
        "recommendation",
        "is_pinned",
    ):
        op.drop_column("client_shortlist_items", column)

    for column in (
        "closed_at",
        "allow_report_download",
        "allow_rating",
        "allow_comments",
        "show_comparison",
        "show_risks",
        "show_salary",
        "show_availability",
        "intro_message",
        "last_invitation_sent_at",
        "access_code_required",
        "access_code_expires_at",
        "access_code_hash",
        "client_contact_company",
        "client_contact_email",
        "client_contact_name",
        "status",
    ):
        op.drop_column("client_shortlists", column)
