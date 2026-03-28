import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.enums import FileStatusEnum
from app.models.file import File
from app.models.vault import Vault


@pytest.fixture(scope="session")
def sync_engine():
    url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(sync_engine) -> Generator[Session, None, None]:
    """
    Provides a real DB session that is rolled back after each test
    so no test data leaks into the dev database.
    """
    connection = sync_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.close()
    try:
        if transaction.is_active:
            transaction.rollback()
    except Exception:
        pass
    finally:
        try:
            connection.close()
        except Exception:
            pass


@pytest.fixture()
def test_vault(db: Session) -> Vault:
    """Creates a real vault row scoped to the test transaction."""
    vault = Vault(
        id=str(uuid.uuid4()),
        user_id="00000000-0000-0000-0000-000000000001",  # fixed test user
        name="Integration Test Vault",
    )
    db.add(vault)
    db.flush()
    return vault


@pytest.fixture()
def test_file(db: Session, test_vault: Vault, tmp_path) -> tuple[File, str]:
    """
    Creates a real file row in PENDING status.
    Also writes a small plain-text file to a temp path for the worker to process.
    Returns (file_row, local_path_to_file).
    """
    import textwrap

    # Write a plain-text file the worker can extract from
    content = (
        textwrap.dedent("""\
        Introduction to Machine Learning

        Machine learning is a branch of artificial intelligence. It enables
        computers to learn from data without being explicitly programmed.

        Supervised Learning

        In supervised learning, the model is trained on labeled data.
        Examples include linear regression and decision trees.

        Unsupervised Learning

        Unsupervised learning finds hidden patterns in unlabeled data.
        Clustering and dimensionality reduction are common techniques.
    """)
        * 5
    )  # repeat to give the chunker enough material

    local_file = tmp_path / "test_notes.txt"
    local_file.write_text(content, encoding="utf-8")

    file_row = File(
        id=str(uuid.uuid4()),
        vault_id=test_vault.id,
        user_id=test_vault.user_id,
        original_name="test_notes.txt",
        file_type="TXT",
        storage_path=f"uploads/{uuid.uuid4()}.txt",
        status=FileStatusEnum.PENDING,
        size_bytes=local_file.stat().st_size,
    )
    db.add(file_row)
    db.flush()

    return file_row, str(local_file)
