"""add gmail senders

Revision ID: 9f07e1eb0c26
Revises: 9f844709d856
Create Date: 2026-09-16 17:21:11.998582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f07e1eb0c26'
down_revision: Union[str, Sequence[str], None] = '9f844709d856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "gmail_senders",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "google_subject_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "encrypted_refresh_token",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_subject_id"),
    )

    op.create_index(
        "ix_gmail_senders_email",
        "gmail_senders",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_gmail_senders_email",
        table_name="gmail_senders",
    )

    op.drop_table("gmail_senders")
