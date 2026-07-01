"""리비전 테이블 추가

Revision ID: 0003_add_revision_table
Revises: 0002_add_document_table
Create Date: 2026-07-01 21:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_revision_table"
down_revision = "0002_add_document_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 리비전 테이블 생성
    op.create_table(
        "revision",
        sa.Column("id", sa.String(255), nullable=False),
        sa.Column("document_id", sa.String(255), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("parent_revision_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name="fk_revision_document_id",
        ),
    )


def downgrade() -> None:
    # 리비전 테이블 삭제
    op.drop_table("revision")
