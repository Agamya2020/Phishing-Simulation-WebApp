"""add sender domains

Revision ID: 9f844709d856
Revises: bb161f704844
Create Date: 2026-09-15 08:47:33.563836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f844709d856'
down_revision: Union[str, Sequence[str], None] = 'bb161f704844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sender_domains",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("resend_domain_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
        sa.UniqueConstraint("resend_domain_id"),
    )
    op.create_index(
        op.f("ix_sender_domains_domain"),
        "sender_domains",
        ["domain"],
        unique=True,
    )
    op.add_column(
        "sender_identities",
        sa.Column("domain_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sender_identities_domain_id",
        "sender_identities",
        "sender_domains",
        ["domain_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_sender_identities_domain_id",
        "sender_identities",
        type_="foreignkey",
    )
    op.drop_column("sender_identities", "domain_id")
    op.drop_index(
        op.f("ix_sender_domains_domain"),
        table_name="sender_domains",
    )
    op.drop_table("sender_domains")
