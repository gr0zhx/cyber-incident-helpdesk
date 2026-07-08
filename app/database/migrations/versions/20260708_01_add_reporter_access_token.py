"""add reporter access token for secure web ticket resume

Revision ID: 20260708_01
Revises: 20260702_01
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa


revision = "20260708_01"
down_revision = "20260702_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incident_tickets",
        sa.Column("reporter_access_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_incident_tickets_reporter_access_token",
        "incident_tickets",
        ["reporter_access_token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_incident_tickets_reporter_access_token", table_name="incident_tickets")
    op.drop_column("incident_tickets", "reporter_access_token")
