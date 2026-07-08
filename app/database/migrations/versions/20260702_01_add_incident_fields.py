"""add incident form fields (Bagian A-D)

Revision ID: 20260702_01
Revises: 20260414_01
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "20260702_01"
down_revision = "20260414_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incident_tickets", sa.Column("media_pelaporan", sa.String(50), nullable=True))
    op.add_column("incident_tickets", sa.Column("incident_time", sa.DateTime(), nullable=True))
    op.add_column("incident_tickets", sa.Column("affected_asset", sa.String(255), nullable=True))
    op.add_column("incident_tickets", sa.Column("cia_confidentiality", sa.Boolean(), nullable=True))
    op.add_column("incident_tickets", sa.Column("cia_integrity", sa.Boolean(), nullable=True))
    op.add_column("incident_tickets", sa.Column("cia_availability", sa.Boolean(), nullable=True))
    op.add_column("incident_tickets", sa.Column("containment_action", sa.Text(), nullable=True))
    op.add_column("incident_tickets", sa.Column("recovery_action", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("incident_tickets", "recovery_action")
    op.drop_column("incident_tickets", "containment_action")
    op.drop_column("incident_tickets", "cia_availability")
    op.drop_column("incident_tickets", "cia_integrity")
    op.drop_column("incident_tickets", "cia_confidentiality")
    op.drop_column("incident_tickets", "affected_asset")
    op.drop_column("incident_tickets", "incident_time")
    op.drop_column("incident_tickets", "media_pelaporan")
