"""add campaign last sent timestamp

Revision ID: 0d8a8624b18d
Revises: 455e8206795a
Create Date: 2026-09-03 16:56:24.152672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d8a8624b18d'
down_revision: Union[str, Sequence[str], None] = '455e8206795a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaigns",
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaigns", "last_sent_at")
