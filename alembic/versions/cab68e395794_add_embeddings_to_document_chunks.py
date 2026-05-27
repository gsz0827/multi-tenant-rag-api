"""add embeddings to document chunks

Revision ID: cab68e395794
Revises: c082a5c741dd
Create Date: 2026-05-27 16:34:31.274748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = 'cab68e395794'
down_revision: Union[str, Sequence[str], None] = 'c082a5c741dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.Vector(dim=1536),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("document_chunks", "embedding")
