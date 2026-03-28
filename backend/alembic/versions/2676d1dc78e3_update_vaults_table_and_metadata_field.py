"""Update vaults table and metadata field

Revision ID: 2676d1dc78e3
Revises: c1a1995a14ac
Create Date: 2026-03-28 11:59:13.161821

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2676d1dc78e3"
down_revision: str | Sequence[str] | None = "c1a1995a14ac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Step 1: Add new columns
    op.add_column(
        "chunks",
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "file_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "vaults",
        sa.Column(
            "vault_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )

    # Step 2: Clean existing data
    op.execute("UPDATE files SET status = UPPER(TRIM(status)) WHERE status IS NOT NULL")
    op.execute(
        "UPDATE files SET status = 'PENDING' WHERE status NOT IN ('PENDING', 'PROCESSING', 'READY', 'FAILED')"
    )
    op.execute(
        "UPDATE files SET file_type = LOWER(TRIM(file_type)) WHERE file_type IS NOT NULL"
    )
    op.execute(
        "UPDATE files SET file_type = 'txt' WHERE file_type NOT IN ('pdf', 'image', 'docx', 'txt', 'note')"
    )

    # Step 3: Add CHECK constraints for status and file_type
    op.execute("""
        ALTER TABLE files
        ADD CONSTRAINT check_file_status
        CHECK (status IN ('PENDING', 'PROCESSING', 'READY', 'FAILED'))
    """)

    op.execute("""
        ALTER TABLE files
        ADD CONSTRAINT check_file_type
        CHECK (file_type IN ('pdf', 'image', 'docx', 'txt', 'note'))
    """)

    # Step 4: Make columns non-nullable with defaults
    op.alter_column(
        "files",
        "status",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default=sa.text("'PENDING'"),
    )

    op.alter_column("files", "file_type", existing_type=sa.TEXT(), nullable=False)

    op.alter_column(
        "chunks",
        "importance_score",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
        existing_server_default=sa.text("1.0"),
    )

    op.alter_column(
        "files",
        "total_chunks",
        existing_type=sa.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("0"),
    )

    op.alter_column(
        "files",
        "total_tokens",
        existing_type=sa.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("0"),
    )

    # Step 5: Drop old indexes
    op.drop_index(
        op.f("idx_chunks_embedding"),
        table_name="chunks",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": "16", "ef_construction": "64"},
        postgresql_using="hnsw",
    )
    op.drop_index(op.f("idx_chunks_file_index"), table_name="chunks")
    op.drop_index(
        op.f("idx_chunks_metadata"), table_name="chunks", postgresql_using="gin"
    )
    op.drop_index(
        op.f("idx_chunks_ts_vector"), table_name="chunks", postgresql_using="gin"
    )
    op.drop_index(op.f("idx_chunks_vault_file"), table_name="chunks")
    op.drop_index(op.f("idx_files_user"), table_name="files")
    op.drop_index(op.f("idx_files_vault_status"), table_name="files")
    op.drop_index(op.f("idx_vaults_user"), table_name="vaults")

    # Step 6: Create new indexes
    op.create_index(op.f("ix_chunks_file_id"), "chunks", ["file_id"], unique=False)
    op.create_index(op.f("ix_files_user_id"), "files", ["user_id"], unique=False)
    op.create_index(op.f("ix_files_vault_id"), "files", ["vault_id"], unique=False)
    op.create_index(op.f("ix_vaults_user_id"), "vaults", ["user_id"], unique=False)

    # Step 7: Drop foreign key constraints (since using Supabase Auth)
    op.drop_constraint(op.f("chunks_vault_id_fkey"), "chunks", type_="foreignkey")
    op.drop_constraint(op.f("files_user_id_fkey"), "files", type_="foreignkey")
    op.drop_constraint(op.f("vaults_user_id_fkey"), "vaults", type_="foreignkey")

    # Step 8: Drop old metadata columns
    op.drop_column("chunks", "metadata")
    op.drop_column("files", "metadata")
    op.drop_column("vaults", "metadata")


def downgrade() -> None:
    """Downgrade schema."""

    # Step 1: Add back old metadata columns
    op.add_column(
        "vaults",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "chunks",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            autoincrement=False,
            nullable=True,
        ),
    )

    # Step 2: Drop CHECK constraints
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_status")
    op.execute("ALTER TABLE files DROP CONSTRAINT IF EXISTS check_file_type")

    # Step 3: Restore foreign keys
    op.create_foreign_key(
        op.f("vaults_user_id_fkey"),
        "vaults",
        "users",
        ["user_id"],
        ["id"],
        referent_schema="auth",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("files_user_id_fkey"),
        "files",
        "users",
        ["user_id"],
        ["id"],
        referent_schema="auth",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("chunks_vault_id_fkey"),
        "chunks",
        "vaults",
        ["vault_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 4: Drop new indexes
    op.drop_index(op.f("ix_vaults_user_id"), table_name="vaults")
    op.drop_index(op.f("ix_files_vault_id"), table_name="files")
    op.drop_index(op.f("ix_files_user_id"), table_name="files")
    op.drop_index(op.f("ix_chunks_file_id"), table_name="chunks")

    # Step 5: Restore old indexes
    op.create_index(op.f("idx_vaults_user"), "vaults", ["user_id"], unique=False)
    op.create_index(
        op.f("idx_files_vault_status"), "files", ["vault_id", "status"], unique=False
    )
    op.create_index(op.f("idx_files_user"), "files", ["user_id"], unique=False)
    op.create_index(
        op.f("idx_chunks_vault_file"), "chunks", ["vault_id", "file_id"], unique=False
    )
    op.create_index(
        op.f("idx_chunks_ts_vector"),
        "chunks",
        ["ts_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("idx_chunks_metadata"),
        "chunks",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("idx_chunks_file_index"), "chunks", ["file_id", "chunk_index"], unique=True
    )
    op.create_index(
        op.f("idx_chunks_embedding"),
        "chunks",
        ["embedding"],
        unique=False,
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": "16", "ef_construction": "64"},
        postgresql_using="hnsw",
    )

    # Step 6: Revert column nullability
    op.alter_column(
        "files",
        "status",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default=sa.text("'PENDING'"),
    )

    op.alter_column("files", "file_type", existing_type=sa.TEXT(), nullable=True)

    op.alter_column(
        "chunks",
        "importance_score",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
        existing_server_default=sa.text("1.0"),
    )

    op.alter_column(
        "files",
        "total_tokens",
        existing_type=sa.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("0"),
    )

    op.alter_column(
        "files",
        "total_chunks",
        existing_type=sa.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("0"),
    )

    # Step 7: Drop new columns
    op.drop_column("chunks", "chunk_metadata")
    op.drop_column("files", "file_metadata")
    op.drop_column("vaults", "vault_metadata")
