"""문서 테이블 추가

Revision ID: 0002_add_document_table
Revises: 0001_initial
Create Date: 2026-07-01 19:41:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_document_table"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 문서 테이블 생성
    op.create_table(
        "document",
        sa.Column("id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.String(500), nullable=False),
        sa.Column("current_revision_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_title", name="uq_document_normalized_title"),
    )


def downgrade() -> None:
    # 문서 테이블 삭제
    op.drop_table("document")
