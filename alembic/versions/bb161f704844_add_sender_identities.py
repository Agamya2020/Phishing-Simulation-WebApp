"""add sender identities

Revision ID: bb161f704844
Revises: 0d8a8624b18d
Create Date: 2026-09-15 01:06:20.523940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb161f704844'
down_revision: Union[str, Sequence[str], None] = '0d8a8624b18d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sender_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_sender_identities_id"),
        "sender_identities",
        ["id"],
        unique=False,
    )
    op.add_column(
        "campaigns",
        sa.Column("sender_identity_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_campaigns_sender_identity_id_sender_identities",
        "campaigns",
        "sender_identities",
        ["sender_identity_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_campaigns_sender_identity_id_sender_identities",
        "campaigns",
        type_="foreignkey",
    )
    op.drop_column("campaigns", "sender_identity_id")
    op.drop_index(
        op.f("ix_sender_identities_id"),
        table_name="sender_identities",
    )
    op.drop_table("sender_identities")
