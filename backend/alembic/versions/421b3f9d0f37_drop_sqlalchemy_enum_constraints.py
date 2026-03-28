"""drop_sqlalchemy_enum_constraints

Revision ID: 421b3f9d0f37
Revises: d67a3d396369
Create Date: 2026-03-28 13:23:12.150149

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "421b3f9d0f37"
down_revision: str | Sequence[str] | None = "d67a3d396369"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the auto-generated SQLAlchemy Enum check constraints
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS files_file_type_check")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS files_status_check")

    # Ensure our named constraints are correct
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_type")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_status")

    op.execute("""
        ALTER TABLE files ADD CONSTRAINT check_file_type
        CHECK (file_type IN ('PDF', 'IMAGE', 'DOCX', 'TXT', 'NOTE'))
    """)
    op.execute("""
        ALTER TABLE files ADD CONSTRAINT check_file_status
        CHECK (status IN ('PENDING', 'PROCESSING', 'READY', 'FAILED'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_type")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_status")
