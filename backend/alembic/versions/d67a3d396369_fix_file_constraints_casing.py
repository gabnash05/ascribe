"""fix_file_constraints_casing

Revision ID: d67a3d396369
Revises: 2676d1dc78e3
Create Date: 2026-03-28 13:16:58.895313

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d67a3d396369"
down_revision: str | Sequence[str] | None = "2676d1dc78e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_status")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_type")

    op.execute("UPDATE files SET status = UPPER(status)")
    op.execute("UPDATE files SET file_type = UPPER(file_type)")

    op.execute("""
        ALTER TABLE files ADD CONSTRAINT check_file_status
        CHECK (status IN ('PENDING', 'PROCESSING', 'READY', 'FAILED'))
    """)
    op.execute("""
        ALTER TABLE files ADD CONSTRAINT check_file_type
        CHECK (file_type IN ('PDF', 'IMAGE', 'DOCX', 'TXT', 'NOTE'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_status")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_type")
