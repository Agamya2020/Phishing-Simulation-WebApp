"""add gmail sender to campaigns

Revision ID: fbfd878a0478
Revises: 9f07e1eb0c26
Create Date: 2026-09-16 23:08:58.145414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbfd878a0478'
down_revision: Union[str, Sequence[str], None] = '9f07e1eb0c26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaigns",
        sa.Column(
            "gmail_sender_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_campaigns_gmail_sender_id",
        "campaigns",
        "gmail_senders",
        ["gmail_sender_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_campaigns_gmail_sender_id",
        "campaigns",
        type_="foreignkey",
    )

    op.drop_column(
        "campaigns",
        "gmail_sender_id",
    )
