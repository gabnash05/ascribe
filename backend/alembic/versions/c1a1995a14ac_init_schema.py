"""init schema

Revision ID: c1a1995a14ac
Revises:
Create Date: 2026-03-23 18:51:36.608085

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a1995a14ac"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Vaults
    op.execute("""
    CREATE TABLE IF NOT EXISTS vaults (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id         UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        name            TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
        description     TEXT,
        vault_metadata  JSONB       DEFAULT '{}'::jsonb,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # Files
    op.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        vault_id        UUID        NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
        user_id         UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        storage_path    EXT        NOT NULL,
        original_name   TEXT        NOT NULL,
        file_type       TEXT        NOT NULL CHECK (file_type IN ('pdf','image','docx','txt','note')),
        mime_type       TEXT,
        size_bytes      BIGINT,
        page_count      INTEGER,
        status          TEXT        NOT NULL DEFAULT 'processing'
                                    CHECK (status IN ('processing','ready','failed')),
        error_message   TEXT,
        total_chunks    INTEGER     DEFAULT 0,
        total_tokens    INTEGER     DEFAULT 0,
        file_metadata   JSONB       DEFAULT '{}'::jsonb,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # Chunks
    op.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
        file_id         UUID        NOT NULL REFERENCES files(id) ON DELETE CASCADE,
        vault_id        UUID        NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
        content         TEXT        NOT NULL,
        chunk_index     INTEGER     NOT NULL,
        page_number     INTEGER,
        section_title   TEXT,
        token_count     INTEGER,
        embedding       VECTOR(384),
        ts_vector       TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
        importance_score    FLOAT       DEFAULT 1.0,
        chunks_metadata JSONB       DEFAULT '{}'::jsonb,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # Indexes
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_file_index ON chunks (file_id, chunk_index);"
    )
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_ts_vector ON chunks USING gin(ts_vector);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING gin(metadata);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_vault_file ON chunks (vault_id, file_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_vault_status ON files (vault_id, status);"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_files_user ON files (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vaults_user ON vaults (user_id);")

    # updated_at trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    BEGIN NEW.updated_at = now(); RETURN NEW; END;
    $$;
    """)

    op.execute("""
    CREATE TRIGGER vaults_updated_at BEFORE UPDATE ON vaults
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)
    op.execute("""
    CREATE TRIGGER files_updated_at BEFORE UPDATE ON files
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)

    # Row Level Security
    op.execute("ALTER TABLE vaults ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE files  ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;")

    op.execute("""
    CREATE POLICY vaults_owner ON vaults
        USING (user_id = auth.uid());
    """)
    op.execute("""
    CREATE POLICY files_owner ON files
        USING (user_id = auth.uid());
    """)
    op.execute("""
    CREATE POLICY chunks_owner ON chunks
        USING (vault_id IN (SELECT id FROM vaults WHERE user_id = auth.uid()));
    """)


def downgrade() -> None:
    # RLS policies
    op.execute("DROP POLICY IF EXISTS chunks_owner ON chunks;")
    op.execute("DROP POLICY IF EXISTS files_owner ON files;")
    op.execute("DROP POLICY IF EXISTS vaults_owner ON vaults;")

    # Triggers
    op.execute("DROP TRIGGER IF EXISTS files_updated_at ON files;")
    op.execute("DROP TRIGGER IF EXISTS vaults_updated_at ON vaults;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at;")

    # Tables (order matters due to foreign keys)
    op.execute("DROP TABLE IF EXISTS chunks;")
    op.execute("DROP TABLE IF EXISTS files;")
    op.execute("DROP TABLE IF EXISTS vaults;")
