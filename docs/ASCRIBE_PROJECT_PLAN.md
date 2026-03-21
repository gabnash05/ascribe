# AScribe — Master Plan of Action & Reusable Prompt Template

---

# PART 1 — Master Plan of Action

---

## Phase 1 — Project Setup

### 1.1 Repository Structure

Use a monorepo layout to keep the small team coordinated under a single Git remote:

```
ascribe/
├── .github/
│   └── workflows/
│       ├── lint.yml
│       ├── test.yml
│       └── deploy.yml
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── vaults.py
│   │   │       ├── files.py
│   │   │       ├── chunks.py
│   │   │       ├── notes.py
│   │   │       └── search.py
│   │   ├── core/             # Config, security, DB session
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── vault.py
│   │   │   ├── file.py
│   │   │   ├── chunk.py
│   │   │   └── note.py
│   │   ├── schemas/          # Pydantic v2 request/response schemas
│   │   │   ├── vault.py
│   │   │   ├── file.py
│   │   │   ├── chunk.py
│   │   │   └── note.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── vault_service.py
│   │   │   ├── file_service.py
│   │   │   ├── search_service.py
│   │   │   └── ai_service.py
│   │   ├── workers/          # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   └── ingestion.py
│   │   ├── pipeline/         # AI/ML pipeline components
│   │   │   ├── extractor.py  # Docling wrapper
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py   # bge-small-en-v1.5 singleton
│   │   │   └── retriever.py  # Hybrid search logic
│   │   └── main.py           # FastAPI app factory
│   ├── migrations/           # Alembic migration files
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios/fetch wrappers
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Route-level page components
│   │   ├── routes/           # TanStack Router file-based route definitions
│   │   ├── stores/           # Zustand state
│   │   ├── hooks/            # Custom React hooks + TanStack Query hooks
│   │   ├── types/            # TypeScript interfaces
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

### 1.2 Git Branching Conventions

With 2–3 developers, keep it simple:

| Branch              | Purpose                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| `main`              | Always deployable. Protected — no direct pushes.                             |
| `dev`               | Integration branch. All feature branches merge here first.                   |
| `feature/<n>`       | One branch per feature or ticket. Merge via PR into `dev`.                   |
| `fix/<n>`           | Bug fixes. Same flow as features.                                            |
| `release/<version>` | Cut from `dev` when deploying to production. Merge into `main` after deploy. |

**Rules:**

- Require at least one reviewer approval before merging into `dev` or `main`.
- Delete feature branches after merge.
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`.

### 1.3 Environment Configuration

Create `.env.example` at the root with every variable documented but no real values:

```dotenv
# ─── Supabase ────────────────────────────────────────────────
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

# ─── PostgreSQL (direct connection for Alembic/SQLAlchemy) ───
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# ─── Redis (self-hosted Docker container) ────────────────────
REDIS_URL=redis://redis:6379/0   # use redis://localhost:6379/0 outside Docker

# ─── OpenAI ──────────────────────────────────────────────────
OPENAI_API_KEY=sk-...

# ─── Application ─────────────────────────────────────────────
SECRET_KEY=<random-64-char-hex>
ENVIRONMENT=development      # development | production
FRONTEND_URL=http://localhost:5173

# ─── Embeddings ──────────────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_CACHE_DIR=./model_cache
```

Each developer copies `.env.example` to `.env` locally and fills in real values. `.env` is gitignored. Never commit secrets.

### 1.4 Local Development Environment

**Prerequisites:** Docker Desktop, Node.js 20+, Python 3.12+.

`docker-compose.yml` orchestrates all backend services locally. Redis and the Celery worker are self-hosted containers — no external managed queue service is used at any stage:

```yaml
version: "3.9"
services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./backend:/app
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    env_file: .env
    volumes:
      - ./backend:/app
      - model_cache:/app/model_cache
    depends_on:
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  model_cache:
  redis_data:
```

> **Note on PostgreSQL:** Do not run Postgres locally in Docker. Use the Supabase-hosted instance for all developers. This avoids schema drift between local and hosted. Use separate Supabase projects for dev and prod.

> **Note on Redis:** Redis runs as a Docker container in every environment — local dev and production. There is no managed Redis service. The `redis_data` volume persists the AOF log so the queue survives container restarts.

**Frontend runs outside Docker** (faster HMR):

```bash
cd frontend && npm install && npm run dev
```

**Backend Python environment (for IDE support and running migrations outside Docker):**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.5 Initial Tooling Setup

#### 1. Clone the Repository

```bash
git clone <repo-url>
cd <project-root>
```

#### 2. Install Dependencies

##### Frontend

```bash
# Create Vite project (if not yet created)
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install core dependencies
npm install @tanstack/react-query zustand axios

# Install TanStack Router
npm install @tanstack/react-router
npm install -D @tanstack/router-devtools @tanstack/router-vite-plugin

# Install Tailwind CSS
npm install -D tailwindcss @tailwindcss/vite

# Install linting + formatting
npm install -D eslint @eslint/js typescript typescript-eslint \
  eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-react-refresh \
  prettier eslint-config-prettier globals

# Initialize shadcn/ui
npx shadcn@latest init

# Add components as needed
npx shadcn@latest add button

cd ..
```

##### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install core dependencies
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
  pydantic-settings celery redis sentence-transformers docling \
  langchain langchain-openai openai supabase python-multipart \
  pgvector

# Install dev tools (linting, formatting, testing)
pip install ruff pytest pytest-asyncio httpx python-dotenv

cd ..
```

#### 3. Install Pre-Commit

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # if available
cd ..
````

#### 4. Install Pre-Commit

Recommended (global):

```bash
pipx install pre-commit
```

Alternative:

```bash
pip install pre-commit
```

#### 5. Enable Git Hooks

```bash
pre-commit install
```

#### 6. Run Initial Lint/Format (Important)

```bash
pre-commit run --all-files
```

---

#### Daily Workflow

```bash
git add .
git commit -m "message"
```

Pre-commit will automatically:

- Lint backend (Ruff)
- Lint frontend (ESLint)
- Format code (Prettier)

---

#### Notes

- Make sure `frontend/node_modules` exists (run `npm install` if errors occur)
- Do not skip hooks unless necessary (`--no-verify`)

#### 7. Configuration Files

##### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { TanStackRouterVite } from '@tanstack/router-vite-plugin'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    TanStackRouterVite(),   // auto-generates routeTree.gen.ts from src/routes/
  ],
})
```

##### src/index.css

```css
@import "tailwindcss";
```

##### src/main.tsx

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import './index.css'

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
```

#### 8. Linting

- Backend: `ruff` (linter + formatter; replaces flake8 + black)
- Frontend: `eslint` + `prettier`
- Pre-commit hooks enforce linting/formatting before each commit

#### 9. Pre-Commit Configuration

```yaml
repos:

  # Backend: Ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
        files: ^backend/
      - id: ruff-format
        files: ^backend/

  # Frontend: ESLint
  - repo: local
    hooks:
      - id: eslint
        name: eslint (frontend)
        entry: npx eslint --fix
        language: system
        files: ^frontend/.*\.(js|jsx|ts|tsx)$

  # Frontend: Prettier
  - repo: local
    hooks:
      - id: prettier
        name: prettier (frontend)
        entry: npx prettier --write
        language: system
        files: ^frontend/.*\.(js|jsx|ts|tsx|json|css|md)$

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

---

## Phase 2 — Infrastructure & Services

### 2.1 Service Inventory

#### Supabase (Auth + PostgreSQL + Storage)

|Attribute|Detail|
|---|---|
|**What it does**|Hosts PostgreSQL with pgvector, file object storage, and user authentication (Google OAuth + email).|
|**How to provision**|Create a project at supabase.com. Enable the `pgvector` extension in the SQL editor: `CREATE EXTENSION IF NOT EXISTS vector;`|
|**Free tier limits**|500 MB database, 1 GB storage, 50,000 monthly active users. Sufficient for development and early usage.|
|**Credentials needed**|`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` (direct Postgres connection string for SQLAlchemy/Alembic).|
|**Important**|Use the Service Role key only server-side (it bypasses Row Level Security). The Anon key is safe to expose on the frontend.|

#### Redis (Self-Hosted Docker Container)

|Attribute|Detail|
|---|---|
|**What it does**|Message queue and result backend for Celery background jobs (file ingestion pipeline).|
|**How to provision (dev)**|Runs as a Docker container via `docker-compose.yml`. No sign-up or external service needed.|
|**How to provision (prod)**|Included in `docker-compose.prod.yml` alongside the API and worker. Deployed as a container on the same host. Redis data is persisted via a named Docker volume with AOF enabled.|
|**Cost**|Zero. Entirely self-hosted.|
|**Free tier limits**|N/A — limited only by host container memory. On free-tier Railway/Fly.io, set `--maxmemory 128mb --maxmemory-policy allkeys-lru` in the Redis command to prevent OOM kills.|
|**Credentials needed**|`REDIS_URL=redis://redis:6379/0` (uses Docker internal networking; the hostname `redis` resolves to the Redis container within the same Compose network).|

#### Celery Worker (Self-Hosted Docker Container)

|Attribute|Detail|
|---|---|
|**What it does**|Processes background file ingestion jobs: OCR, chunking, embedding, and database writes.|
|**How to provision**|Built from `Dockerfile.worker` and run as a container alongside the API and Redis in both dev and prod Docker Compose files.|
|**Cost**|Zero. Co-hosted with the API on the same Railway/Fly.io service or VM.|
|**Important**|The worker needs a persistent volume for the `model_cache` directory so `bge-small-en-v1.5` (130 MB) is downloaded only once. Mount the volume at `/app/model_cache` in the Compose file.|

#### OpenAI (LLM)

|Attribute|Detail|
|---|---|
|**What it does**|Powers summarization, Q&A, and flashcard generation via GPT-4o-nano.|
|**How to provision**|Create an API key at platform.openai.com.|
|**Cost**|GPT-4o-nano: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens. Very cheap for a student tool. Set a hard spend limit in OpenAI dashboard.|
|**Credentials needed**|`OPENAI_API_KEY`|

#### Vercel (Frontend Hosting)

|Attribute|Detail|
|---|---|
|**What it does**|Hosts the React frontend. Automatic preview deployments on every PR.|
|**How to provision**|Connect the GitHub repo at vercel.com. Set `frontend/` as the root directory.|
|**Free tier limits**|Unlimited personal projects, 100 GB bandwidth/month, preview deployments.|
|**Env vars needed**|`VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`|

#### Railway or Fly.io (Backend + Worker + Redis Hosting)

|Attribute|Detail|
|---|---|
|**What it does**|Hosts all three backend containers — FastAPI API, Celery worker, and Redis — using the production Docker Compose file.|
|**Recommended choice**|**Railway** for simplicity. Deploy using `docker-compose.prod.yml` or as individual services from the same repo. Free tier: $5/month credit (covers small workloads).|
|**Alternative**|**Fly.io** offers 3 shared-CPU VMs free. More configuration but more generous. Deploy each container as a separate Fly app within the same private network so they can communicate via internal hostnames.|
|**Important**|Add a persistent volume to the worker service for `model_cache`. Add a persistent volume to the Redis service for `redis_data`. Both Railway and Fly.io support volume mounts on their free tiers (1 GB each).|
|**Credentials needed**|All backend env vars set as platform environment variables. `REDIS_URL` uses the internal Docker network hostname (`redis`) — no external URL needed.|

#### GitHub Actions (CI/CD)

|Attribute|Detail|
|---|---|
|**What it does**|Runs lint, tests, and deployment on push.|
|**How to provision**|Free for public repos and 2,000 minutes/month for private repos.|
|**Credentials needed**|Store `RAILWAY_TOKEN` (or Fly deploy token) and `VERCEL_TOKEN` as GitHub Secrets.|

---

## Phase 3 — Database Design & Migrations

### 3.1 Full Schema

Execute the following in the Supabase SQL editor (or via Alembic migrations):

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── VAULTS ──────────────────────────────────────────────────
CREATE TABLE vaults (
  id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name         TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── FILES ───────────────────────────────────────────────────
CREATE TABLE files (
  id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  vault_id       UUID        NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
  user_id        UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  storage_path   TEXT        NOT NULL,
  original_name  TEXT        NOT NULL,
  file_type      TEXT        NOT NULL CHECK (file_type IN ('pdf','image','docx','txt','note')),
  mime_type      TEXT,
  size_bytes     BIGINT,
  page_count     INTEGER,
  status         TEXT        NOT NULL DEFAULT 'processing'
                             CHECK (status IN ('processing','ready','failed')),
  error_message  TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── CHUNKS ──────────────────────────────────────────────────
CREATE TABLE chunks (
  id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_id        UUID        NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  vault_id       UUID        NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
  content        TEXT        NOT NULL,
  chunk_index    INTEGER     NOT NULL,
  page_number    INTEGER,
  section_title  TEXT,
  token_count    INTEGER,
  embedding      VECTOR(384),
  ts_vector      TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── NOTES ───────────────────────────────────────────────────
CREATE TABLE notes (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  vault_id    UUID        NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title       TEXT,
  content     TEXT        NOT NULL,
  ingested    BOOLEAN     NOT NULL DEFAULT false,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── INDEXES ─────────────────────────────────────────────────
-- Vector similarity (HNSW for fast ANN search)
CREATE INDEX idx_chunks_embedding ON chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Full-text keyword search
CREATE INDEX idx_chunks_ts_vector ON chunks USING gin (ts_vector);

-- Vault-scoped file listing
CREATE INDEX idx_files_vault_status ON files (vault_id, status);

-- Vault-scoped chunk retrieval
CREATE INDEX idx_chunks_vault_file ON chunks (vault_id, file_id);

-- User's vault listing
CREATE INDEX idx_vaults_user ON vaults (user_id);

-- Note lookup by vault
CREATE INDEX idx_notes_vault ON notes (vault_id);

-- ─── UPDATED_AT TRIGGER ──────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

CREATE TRIGGER vaults_updated_at BEFORE UPDATE ON vaults
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER files_updated_at BEFORE UPDATE ON files
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER notes_updated_at BEFORE UPDATE ON notes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── ROW LEVEL SECURITY ──────────────────────────────────────
ALTER TABLE vaults ENABLE ROW LEVEL SECURITY;
ALTER TABLE files  ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes  ENABLE ROW LEVEL SECURITY;

-- Vaults: users see only their own
CREATE POLICY vaults_owner ON vaults
  USING (user_id = auth.uid());

-- Files: users see only files in their own vaults
CREATE POLICY files_owner ON files
  USING (user_id = auth.uid());

-- Chunks: users see only chunks from their own vaults
CREATE POLICY chunks_owner ON chunks
  USING (vault_id IN (SELECT id FROM vaults WHERE user_id = auth.uid()));

-- Notes: users see only their own notes
CREATE POLICY notes_owner ON notes
  USING (user_id = auth.uid());
```

> **RLS Note:** The backend makes database calls using the Supabase Service Role key (bypasses RLS) via SQLAlchemy's async connection pool. RLS is primarily a safety net if any queries ever go through the Anon key path.

### 3.2 Migration Strategy

Use **Alembic** for schema migrations managed in code.

```bash
# Initialize (run once)
cd backend
alembic init migrations

# Generate a migration from ORM model changes
alembic revision --autogenerate -m "add_chunks_table"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

**`alembic.ini`** points to `DATABASE_URL` from the environment. Keep migration files committed. Never manually edit the database schema after the first migration.

**Important:** The `VECTOR(384)` column type requires the `pgvector` SQLAlchemy extension. Add to `database.py`:

```python
from pgvector.sqlalchemy import Vector
```

And in the Chunk ORM model:

```python
embedding = Column(Vector(384))
```

---

## Phase 4 — Backend Development

Build in this order. Each module depends on the one above it.

### 4.1 Module 1: Core Foundation

**Files to build:**

- `app/core/config.py` — Pydantic `BaseSettings` class that reads all env vars. Single source of truth for configuration. Export a `settings` singleton.
- `app/core/database.py` — Async SQLAlchemy engine + session factory using `asyncpg`. Expose `get_db` dependency for FastAPI route injection.
- `app/core/security.py` — JWT verification using Supabase's JWKS endpoint. Expose `get_current_user` FastAPI dependency that extracts and validates the user ID from the Bearer token on every protected request.
- `app/main.py` — FastAPI app factory. Register all routers with `/api/v1` prefix. Add CORS middleware allowing the frontend origin. Add lifespan event to warm the embedding model on startup.

### 4.2 Module 2: ORM Models

**Files to build:**

- `app/models/vault.py` — `Vault` SQLAlchemy model mapping to the `vaults` table.
- `app/models/file.py` — `File` model mapping to `files`.
- `app/models/chunk.py` — `Chunk` model with `Vector(384)` column from `pgvector.sqlalchemy`.
- `app/models/note.py` — `Note` model mapping to `notes`.
- `app/models/__init__.py` — Import all models so Alembic's `autogenerate` detects them.

### 4.3 Module 3: Pydantic Schemas

**Files to build:**

- `app/schemas/vault.py` — `VaultCreate`, `VaultUpdate`, `VaultResponse`.
- `app/schemas/file.py` — `FileResponse` (upload response, file listing).
- `app/schemas/chunk.py` — `ChunkSearchResult` (content + source metadata).
- `app/schemas/note.py` — `NoteCreate`, `NoteUpdate`, `NoteResponse`.
- `app/schemas/search.py` — `SearchRequest` (query string, top_k), `SearchResponse`.
- `app/schemas/ai.py` — `SummarizeRequest`, `GenerateQARequest`, `AIResponse`.

### 4.4 Module 4: Background Job Infrastructure

**Files to build:**

- `app/workers/celery_app.py` — Celery application instance configured with the self-hosted Redis broker and result backend. Set `task_serializer = 'json'`.
- `app/workers/ingestion.py` — The `ingest_file` Celery task. Accepts `file_id: str`. Orchestrates the full pipeline: extract → clean → chunk → embed → bulk insert. Updates `files.status` on completion or failure. This is the most important worker file.
- `Dockerfile.worker` — Separate Dockerfile for the Celery worker. Installs all backend dependencies. The `CMD` runs `celery -A app.workers.celery_app worker`.

### 4.5 Module 5: API Routes

Build routes in this recommended order:

**`app/api/v1/vaults.py`**

- `POST /vaults` — Create vault
- `GET /vaults` — List user's vaults
- `GET /vaults/{vault_id}` — Get single vault
- `PUT /vaults/{vault_id}` — Update vault name/description
- `DELETE /vaults/{vault_id}` — Delete vault (cascades to files/chunks/notes)

**`app/api/v1/files.py`**

- `POST /vaults/{vault_id}/files` — Upload file (multipart). Save to Supabase Storage, insert `files` row with status `processing`, enqueue `ingest_file` Celery task. Return `file_id` immediately.
- `GET /vaults/{vault_id}/files` — List files in vault with status.
- `GET /vaults/{vault_id}/files/{file_id}` — Get single file metadata.
- `DELETE /vaults/{vault_id}/files/{file_id}` — Delete file record + storage object + cascades chunks.
- `GET /vaults/{vault_id}/files/{file_id}/status` — Polling endpoint for ingestion status. Frontend polls this until status is `ready` or `failed`.

**`app/api/v1/notes.py`**

- `POST /vaults/{vault_id}/notes` — Create note
- `GET /vaults/{vault_id}/notes` — List notes
- `PUT /vaults/{vault_id}/notes/{note_id}` — Update note content
- `DELETE /vaults/{vault_id}/notes/{note_id}` — Delete note
- `POST /vaults/{vault_id}/notes/{note_id}/ingest` — Trigger ingestion of a note into the knowledge base (sets `ingested = true`, enqueues a lightweight embed task)

**`app/api/v1/search.py`**

- `POST /vaults/{vault_id}/search` — Hybrid search. Body: `{ query, top_k }`. Returns ranked chunks with source metadata.

**`app/api/v1/ai.py`**

- `POST /vaults/{vault_id}/summarize` — Summarize vault or specific files.
- `POST /vaults/{vault_id}/generate-qa` — Generate Q&A flashcard pairs.
- `POST /vaults/{vault_id}/quiz` — Generate a practice quiz.

### 4.6 Module 6: Service Layer

**Files to build:**

- `app/services/vault_service.py` — CRUD operations for vaults with ownership checks.
- `app/services/file_service.py` — Upload to Supabase Storage (`supabase-py` client), insert file record, enqueue Celery task.
- `app/services/search_service.py` — Orchestrates hybrid search: embed query → run hybrid SQL → rerank by combining scores → return top-K with metadata.
- `app/services/ai_service.py` — Retrieves context chunks, assembles prompt, calls GPT-4o-nano via `langchain-openai`. Contains prompt templates for each task type.

---

## Phase 5 — AI / ML Pipeline

### 5.1 Document Extraction — `app/pipeline/extractor.py`

**Library:** `docling`

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

def extract_text(file_path: str) -> dict:
    """
    Returns a dict with:
      - 'text': full extracted text (markdown-formatted)
      - 'pages': list of {page_number, text} dicts
      - 'metadata': title, author if available
    """
    result = converter.convert(file_path)
    return {
        "text": result.document.export_to_markdown(),
        "pages": _extract_pages(result),
    }
```

Docling handles PDFs, DOCX, images, and handwritten notes (OCR) in a single call. No preprocessing pipeline needed.

**Tricky point:** Docling downloads its own models on first run. In the Docker worker, call a warm-up conversion on startup to download models before any real requests arrive. Pre-build the model cache into the Docker image or use a persistent volume.

### 5.2 Chunking Strategy — `app/pipeline/chunker.py`

Use **recursive character splitting** with LangChain's `RecursiveCharacterTextSplitter`:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,         # tokens ≈ characters / 4
    chunk_overlap=64,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Design decisions:**

- **512 character chunks:** Balances context (enough for meaningful retrieval) with embedding quality (bge-small performs best on short-to-medium inputs).
- **64-character overlap:** Prevents context loss at chunk boundaries.
- **Separator priority:** Double newline → single newline → sentence end → word boundary. This preserves paragraph and sentence semantics.
- **Page-aware chunking:** After splitting, tag each chunk with its source page by tracking character offsets against the page-split text.

### 5.3 Embedding Model — `app/pipeline/embedder.py`

**Model:** `BAAI/bge-small-en-v1.5` via `sentence-transformers`

**Singleton loading pattern** (load once per worker process):

```python
from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        cache_folder=settings.EMBEDDING_CACHE_DIR
    )
    return model

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False
    )
    return embeddings.tolist()

def embed_query(query: str) -> list[float]:
    # BGE requires this prefix for asymmetric retrieval
    return embed_texts([f"Represent this sentence for searching: {query}"])[0]
```

**Important:** BGE uses different prefixes for documents vs queries in asymmetric retrieval. Documents are embedded without a prefix; queries use `"Represent this sentence for searching: "`. This significantly improves retrieval quality.

### 5.4 Hybrid Search — `app/pipeline/retriever.py`

The hybrid search combines pgvector ANN search with PostgreSQL full-text search using Reciprocal Rank Fusion (RRF) to merge result lists:

```python
HYBRID_SEARCH_SQL = """
WITH semantic AS (
  SELECT id, content, file_id, vault_id, page_number, section_title,
         (1 - (embedding <=> :query_vec::vector)) AS semantic_score
  FROM chunks
  WHERE vault_id = :vault_id
  ORDER BY embedding <=> :query_vec::vector
  LIMIT :top_k
),
keyword AS (
  SELECT id, content, file_id, vault_id, page_number, section_title,
         ts_rank(ts_vector, plainto_tsquery('english', :query_text)) AS keyword_score
  FROM chunks
  WHERE vault_id = :vault_id
    AND ts_vector @@ plainto_tsquery('english', :query_text)
  ORDER BY keyword_score DESC
  LIMIT :top_k
),
merged AS (
  SELECT COALESCE(s.id, k.id)            AS id,
         COALESCE(s.content, k.content)  AS content,
         COALESCE(s.file_id, k.file_id)  AS file_id,
         COALESCE(s.page_number, k.page_number) AS page_number,
         COALESCE(s.section_title, k.section_title) AS section_title,
         (1.0 / (60 + COALESCE(s_rank.rank, 999))) +
         (1.0 / (60 + COALESCE(k_rank.rank, 999))) AS rrf_score
  FROM semantic s
  FULL OUTER JOIN keyword k ON s.id = k.id
  LEFT JOIN (SELECT id, ROW_NUMBER() OVER (ORDER BY semantic_score DESC) AS rank FROM semantic) s_rank ON s_rank.id = COALESCE(s.id, k.id)
  LEFT JOIN (SELECT id, ROW_NUMBER() OVER (ORDER BY keyword_score DESC) AS rank FROM keyword) k_rank ON k_rank.id = COALESCE(s.id, k.id)
)
SELECT m.*, f.original_name
FROM merged m
JOIN files f ON f.id = m.file_id
ORDER BY rrf_score DESC
LIMIT :top_k;
"""
```

**RRF explanation:** Rather than naively averaging scores (which have different scales), RRF converts each result list into ranks and combines `1/(k + rank)` values. k=60 is the standard constant that dampens the influence of lower-ranked results.

### 5.5 LLM Generation — `app/services/ai_service.py`

**Model:** `gpt-4o-nano` via LangChain

**Prompt templates for each task:**

**Summarization:**

```
You are a study assistant. Summarize the following content from the student's
notes and documents. Be concise and organized. Focus on key concepts, definitions,
and relationships.

CONTENT FROM VAULT:
{context}

Provide a structured summary with clear sections. Ground every claim in the
provided content. Do not invent or hallucinate information.
```

**Q&A / Flashcard Generation:**

```
You are a study assistant. Based on the following content, generate {count}
high-quality question-answer pairs suitable for flashcard study.

CONTENT:
{context}

Format your response as a JSON array:
[{{"question": "...", "answer": "...", "difficulty": "easy|medium|hard"}}]

Focus on testable concepts, definitions, and key facts. Use only information
from the provided content.
```

**Quiz Generation:**

```
You are a study assistant. Generate a {count}-question multiple-choice quiz
based on the following content.

CONTENT:
{context}

Format as JSON:
[{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
   "correct": "A", "explanation": "..."}}]

Ensure questions test understanding, not just recall.
```

**Context Assembly Strategy:**

- For **search**: Use top-K chunks directly.
- For **summarization of full vault**: Retrieve all chunks ordered by `chunk_index`, split into batches, use map-reduce pattern (summarize each batch, then summarize the summaries).
- For **Q&A generation**: Retrieve top-K chunks by semantic similarity to a general topic query, or use all chunks for a specific document.

---

## Phase 6 — Frontend Development

Build in this order to always have a working UI for the current phase.

### 6.1 Foundation Setup

1. Install Tailwind CSS V4 with the `@tailwindcss/vite` plugin. Configure it in `vite.config.ts` as shown in Phase 1.5. Add `@import "tailwindcss";` to `src/index.css`. There is no `tailwind.config.ts` in V4 — theme customization is done via `@theme` directives directly in your CSS file.
2. Run `npx shadcn@latest init` and add initial components: `Button`, `Input`, `Card`, `Dialog`, `DropdownMenu`, `Badge`, `Skeleton`, `Textarea`, `Toast`.
3. Create `src/api/client.ts` — Axios instance with base URL from env var, interceptor to attach Supabase auth token from session to every request's `Authorization` header.
4. Create `src/stores/authStore.ts` — Zustand store holding `user`, `session`, `isLoading`. Syncs with Supabase's `onAuthStateChange`.
5. Create `src/hooks/useAuth.ts` — Wraps auth store. Exposes `signInWithGoogle()`, `signOut()`, `user`.
6. Set up TanStack Router using file-based routing. The `@tanstack/router-vite-plugin` auto-generates `routeTree.gen.ts` from files created under `src/routes/`. Route files follow the naming convention below.

**TanStack Router file-based route structure:**

```
src/routes/
├── __root.tsx          # Root layout (Navbar, auth guard via beforeLoad)
├── index.tsx           # "/" — landing/redirect
├── login.tsx           # "/login"
├── dashboard.tsx       # "/dashboard"
└── vault/
    └── $vaultId.tsx    # "/vault/$vaultId" — dynamic segment
```

Each route file exports a `Route` created with `createFileRoute`:

```typescript
// src/routes/dashboard.tsx
import { createFileRoute } from '@tanstack/react-router'
import { DashboardPage } from '../pages/DashboardPage'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})
```

Navigation uses TanStack Router's `<Link>` and `useNavigate` — never `react-router-dom`:

```typescript
import { Link, useNavigate } from '@tanstack/react-router'

// Declarative link with type-safe params
<Link to="/vault/$vaultId" params={{ vaultId: id }}>Open Vault</Link>

// Programmatic navigation
const navigate = useNavigate()
navigate({ to: '/dashboard' })

// Reading dynamic params (inside the route component)
const { vaultId } = Route.useParams()
```

### 6.2 Page: Auth (`/login`)

**What it shows:** Centered card with app logo, tagline, and "Sign in with Google" button.

**API calls:** Calls `supabase.auth.signInWithOAuth({ provider: 'google' })`. Supabase handles the redirect and session. After auth, redirect to `/dashboard` using `useNavigate`.

**Components to build:** `LoginPage`, `AuthCard`.

### 6.3 Page: Dashboard (`/dashboard`)

**What it shows:** Grid/list of the user's vaults. Empty state if none. "Create Vault" button opens a dialog.

**API calls:**

- `GET /api/v1/vaults` via `useQuery(['vaults'])`.
- `POST /api/v1/vaults` via `useMutation` to create a vault.
- `DELETE /api/v1/vaults/:id` via `useMutation`.

**Components to build:** `DashboardPage`, `VaultCard`, `CreateVaultDialog`, `EmptyVaultsState`.

### 6.4 Page: Vault View (`/vault/$vaultId`)

This is the main application page. Build it with a two-panel layout. Read the vault ID from the route using `Route.useParams()`.

**Left Panel — File Manager:**

- File list with status indicators (processing spinner, ready checkmark, failed badge).
- Upload button that triggers a file input. Shows upload progress.
- Delete file button per row.

**Right Panel — AI Workspace (tabbed):**

- **Tab 1: Search** — Query input + results list showing chunk content + source attribution (filename, page).
- **Tab 2: Summarize** — Button to summarize vault or selected files. Streaming or loading state. Rendered markdown output.
- **Tab 3: Flashcards** — Generate button + rendered flashcard deck (flip animation, difficulty badges).
- **Tab 4: Quiz** — Generate button + interactive multiple-choice quiz with answer reveal.
- **Tab 5: Notes** — Text editor for personal notes. Save + "Ingest" button per note.

**API calls:**

- `GET /api/v1/vaults/:id/files` — File list.
- `POST /api/v1/vaults/:id/files` — Upload (multipart form).
- `GET /api/v1/vaults/:id/files/:fileId/status` — Polling for ingestion status. Use `refetchInterval` in TanStack Query until status is `ready` or `failed`.
- `DELETE /api/v1/vaults/:id/files/:fileId`
- `POST /api/v1/vaults/:id/search`
- `POST /api/v1/vaults/:id/summarize`
- `POST /api/v1/vaults/:id/generate-qa`
- `POST /api/v1/vaults/:id/quiz`
- Full CRUD for notes.

**Components to build:** `VaultPage`, `FileManager`, `FileUploadZone` (drag-and-drop via `react-dropzone`), `FileListItem`, `SearchPanel`, `SearchResultCard`, `SummarizePanel`, `FlashcardDeck`, `FlashcardItem`, `QuizPanel`, `QuizQuestion`, `NotesPanel`, `NoteEditor`.

### 6.5 Global Components

- `Navbar` — App logo, user avatar with dropdown (sign out).
- `AuthGuard` — Implemented as a `beforeLoad` hook in `__root.tsx`. Checks Zustand auth state and throws a `redirect` to `/login` if no session. This is the TanStack Router way — no separate `<ProtectedRoute>` wrapper component needed.
- `ErrorBoundary` — Catches render errors gracefully.
- `LoadingSpinner` — Reusable centered spinner.

**Auth guard pattern with TanStack Router:**

```typescript
// src/routes/__root.tsx
import { createRootRoute, Outlet, redirect } from '@tanstack/react-router'
import { useAuthStore } from '../stores/authStore'
import { Navbar } from '../components/Navbar'

export const Route = createRootRoute({
  beforeLoad: ({ location }) => {
    const { session } = useAuthStore.getState()
    const publicPaths = ['/login', '/']
    if (!session && !publicPaths.includes(location.pathname)) {
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
  },
  component: () => (
    <>
      <Navbar />
      <Outlet />
    </>
  ),
})
```

### 6.6 State Management Notes

- **Server state** (vault list, file list, search results): TanStack Query. Do not put this in Zustand.
- **UI state** (which tab is active, whether a dialog is open): Local `useState`.
- **Auth state** (user session): Zustand `authStore`.
- **Route params** (current vault ID): `Route.useParams()` from TanStack Router, not global state.

---

## Phase 7 — Integration & Wiring

### 7.1 Auth Flow End-to-End

1. User clicks "Sign in with Google" → Supabase OAuth redirect.
2. Supabase issues a JWT (signed with Supabase's private key).
3. Frontend stores the JWT in memory (Supabase JS SDK handles this).
4. Every API request includes `Authorization: Bearer <jwt>`.
5. `app/core/security.py` verifies the JWT against Supabase's JWKS endpoint (`https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`).
6. Extracts `sub` (user UUID) and injects into route handlers as `current_user`.

**Tricky point:** Supabase JWTs expire. The Supabase JS SDK auto-refreshes the session token silently. Make sure the Axios interceptor always reads `supabase.auth.getSession()` freshly on each request, not a stale cached value.

### 7.2 File Upload & Ingestion Flow End-to-End

1. Frontend sends `POST /vaults/:id/files` with `multipart/form-data`.
2. FastAPI receives file bytes in memory.
3. `file_service.upload_file()`:
    - Uploads bytes to Supabase Storage at path `{user_id}/{vault_id}/{uuid}_{original_name}`.
    - Inserts `files` row with `status = 'processing'`.
    - Enqueues `ingest_file.delay(file_id)` Celery task. The task lands in the self-hosted Redis queue.
    - Returns `{ file_id, status: 'processing' }` immediately (non-blocking).
4. Frontend starts polling `GET /files/:id/status` every 3 seconds.
5. Celery worker (running as a Docker container alongside Redis) picks up the task:
    - Downloads file from Supabase Storage to a temp directory.
    - Calls `extractor.extract_text(temp_path)`.
    - Calls `chunker.split(extracted_text)`.
    - Calls `embedder.embed_texts(chunks)` in batches.
    - Bulk inserts all chunk records into `chunks` table.
    - Updates `files.status = 'ready'` (or `'failed'` with error message on exception).
    - Cleans up temp file.
6. Frontend poll detects `'ready'` → stops polling → refreshes file list → shows ready indicator.

**Tricky point:** Supabase Storage download in the worker requires the Service Role key. Use `supabase-py` with the service role client, not the anon client.

### 7.3 Search Flow End-to-End

1. User types query in Search tab → `POST /vaults/:id/search` with `{ query, top_k: 10 }`.
2. FastAPI route calls `search_service.search(vault_id, query)`.
3. `search_service`:
    - Calls `embedder.embed_query(query)` → 384-dim vector.
    - Executes the hybrid SQL query with both the vector and query text.
    - Returns list of `ChunkSearchResult` with content + source metadata.
4. Frontend renders results in `SearchResultCard` components showing content excerpt + "Source: filename, page X".

### 7.4 AI Generation Flow End-to-End

1. User clicks "Summarize" / "Generate Flashcards" etc.
2. Frontend sends `POST /vaults/:id/summarize` (or equivalent).
3. FastAPI route calls `ai_service.summarize(vault_id, options)`.
4. `ai_service`:
    - Retrieves relevant chunks via `search_service` or full vault retrieval.
    - Assembles context string.
    - Calls GPT-4o-nano with the appropriate prompt template via LangChain.
    - Returns structured response.
5. Frontend renders the output (markdown for summary, card flip UX for flashcards, interactive for quiz).

**Tricky point — response time:** LLM calls can take 5–20 seconds. Use a streaming response if possible: FastAPI `StreamingResponse` + `Server-Sent Events` on the frontend for summary generation. For flashcards/quiz (which need JSON), accept the full wait with a loading state.

---

## Phase 8 — Testing Strategy

Keep tests lean but cover every critical path.

### 8.1 Backend Tests

**Tool:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient`

**Unit tests (fast, no DB):**

- `test_chunker.py` — Assert chunk sizes are within bounds, overlap is preserved, empty input is handled.
- `test_embedder.py` — Assert output vector length is 384, normalize=True produces unit vectors, batch embedding matches single embedding.
- `test_prompts.py` — Assert prompt templates render correctly with test inputs.

**Integration tests (requires test DB):**

- `test_ingestion.py` — Upload a small test PDF, run the full Celery task synchronously (use `task.apply()` not `.delay()`), assert chunks are inserted and file status is `ready`.
- `test_search.py` — Insert known chunks, query for them, assert they appear in top-3 results.
- `test_api_auth.py` — Assert that all protected routes return 401 without a token.
- `test_vaults_api.py` — Full CRUD cycle for vaults.
- `test_files_api.py` — Upload + status check + delete cycle.

**Use a separate test Supabase project** (free tier allows multiple projects). Set `DATABASE_URL` to the test project in test environment. Redis for tests uses the local Docker container — no additional setup needed.

### 8.2 Frontend Tests

**Tools:** `Vitest` + `@testing-library/react`

**Component tests:**

- `SearchPanel.test.tsx` — Renders results correctly, shows empty state.
- `FlashcardDeck.test.tsx` — Card flip works, navigation between cards works.
- `FileListItem.test.tsx` — Shows correct status badge per status value.
- `CreateVaultDialog.test.tsx` — Form validation, submit calls mutation.

**Mock all API calls with `msw` (Mock Service Worker).** Do not make real network calls in tests.

**TanStack Router in tests:** Use `createMemoryHistory` + `createRouter` to wrap components under test:

```typescript
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router'
import { routeTree } from '../routeTree.gen'

const router = createRouter({
  routeTree,
  history: createMemoryHistory({ initialEntries: ['/dashboard'] }),
})
render(<RouterProvider router={router} />)
```

### 8.3 Critical Paths That Must Pass Before Calling the App Functional

1. User can sign in with Google and access the dashboard.
2. User can create a vault.
3. User can upload a PDF and it reaches `status = 'ready'` within 2 minutes.
4. User can search the vault and receive results with source attribution.
5. User can generate a summary and receive a coherent, grounded response.
6. User can generate flashcards and receive valid Q&A pairs.
7. User can create and ingest a personal note.
8. Deleting a vault cascades and removes all files, chunks, and notes.

---

## Phase 9 — Deployment

### 9.1 Pre-Deployment Checklist

- [ ] All environment variables documented in `.env.example`.
- [ ] `ENVIRONMENT=production` triggers any production-only guards (e.g., stricter CORS).
- [ ] Supabase **production project** created (separate from dev project).
- [ ] All Alembic migrations applied to the production database.
- [ ] OpenAI billing limit set.
- [ ] `docker-compose.prod.yml` tested locally before pushing to host.

### 9.2 Frontend — Vercel

1. Push repo to GitHub.
2. Go to vercel.com → New Project → Import GitHub repo.
3. Set **Root Directory** to `frontend`.
4. Set **Build Command** to `npm run build`.
5. Set **Output Directory** to `dist`.
6. Add environment variables in Vercel dashboard:
    - `VITE_API_URL` → your Railway API URL
    - `VITE_SUPABASE_URL` → production Supabase URL
    - `VITE_SUPABASE_ANON_KEY` → production anon key
7. Deploy. Vercel auto-deploys on every push to `main`.

### 9.3 Backend — Production Docker Compose

All three backend services (API, Celery worker, Redis) are defined in `docker-compose.prod.yml` and deployed together. No external queue service is involved at any stage:

```yaml
version: "3.9"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env.prod
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    env_file: .env.prod
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - model_cache:/app/model_cache
    depends_on:
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=1

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: >
      redis-server --appendonly yes
      --maxmemory 128mb
      --maxmemory-policy allkeys-lru

volumes:
  model_cache:
  redis_data:
```

> All three services communicate over Docker's internal network. `REDIS_URL` uses the hostname `redis` — no external Redis URL, no managed service, no cost.

### 9.4 Backend API + Worker + Redis — Railway

1. Go to railway.app → New Project → Deploy from GitHub.
2. Select the monorepo. Set **Root Directory** to `backend`.
3. Configure Railway to use `docker-compose.prod.yml`. Alternatively deploy each service individually using its respective Dockerfile.
4. Add all backend environment variables in Railway's Variables tab. Set `REDIS_URL=redis://redis:6379/0`.
5. Add **Volume mounts** for both `model_cache` (worker) and `redis_data` (redis) in Railway's volume UI.
6. Note the generated `*.up.railway.app` URL for the API — this becomes `VITE_API_URL` in Vercel.

### 9.5 Google OAuth for Production

1. In Google Cloud Console → Credentials → OAuth 2.0 Client IDs.
2. Add your Vercel production URL to **Authorized JavaScript origins**.
3. Add `https://<project-ref>.supabase.co/auth/v1/callback` to **Authorized redirect URIs**.
4. In Supabase dashboard → Auth → Providers → Google: add Client ID and Secret.

### 9.6 GitHub Actions CI/CD

`.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        run: |
          curl -fsSL https://railway.app/install.sh | sh
          railway up --service api --detach
          railway up --service worker --detach
          railway up --service redis --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  # Vercel deploys automatically via its GitHub integration
```

---

## Phase 10 — Verification & QA Checklist

Work through these checks in order. Do not mark the app "done" until all pass.

### Auth & Access

- [ ] Landing page redirects unauthenticated users to `/login`.
- [ ] "Sign in with Google" completes and lands on `/dashboard`.
- [ ] Signing out clears the session and redirects to `/login`.
- [ ] Pasting a vault URL while signed out redirects to login then back after auth.
- [ ] API returns 401 for any protected endpoint called without a token.

### Vault Management

- [ ] Can create a vault with a name and optional description.
- [ ] Vault appears in dashboard grid after creation.
- [ ] Can rename a vault.
- [ ] Deleting a vault removes it from the dashboard.
- [ ] Deleted vault's files/chunks/notes are gone from the database (verify via Supabase table editor).

### File Ingestion

- [ ] Upload a PDF → status shows "Processing" immediately.
- [ ] Status transitions to "Ready" within 2 minutes.
- [ ] Upload a DOCX → same flow.
- [ ] Upload an image with printed text → OCR extracts readable text (check by searching for a known word from the image).
- [ ] Upload a file that is corrupt or unsupported → status shows "Failed" with an error message visible in the UI.
- [ ] Deleting a ready file removes its chunks from the database (verify row count in chunks table drops).

### Search

- [ ] Search for a term known to be in an uploaded document → it appears in results.
- [ ] Each result shows the source filename and page number.
- [ ] Search for a term not in any document → empty state is shown, not an error.
- [ ] Search returns results from only the current vault (not other vaults the user has).

### AI Features

- [ ] Summarize vault → output is coherent and references content from uploaded files.
- [ ] Summarize a single file → output is specific to that file.
- [ ] Generate flashcards → at least the requested number of Q&A pairs are returned, all grounded in vault content.
- [ ] Generate quiz → multiple-choice questions render correctly, selecting answers works, reveal explanation works.
- [ ] All AI outputs fail gracefully (show error toast) if the vault has no indexed content.

### Notes

- [ ] Can create a note with a title and content.
- [ ] Note auto-saves or save button works.
- [ ] Clicking "Ingest" on a note → note becomes searchable within seconds.
- [ ] Search for a phrase from the note → it appears in results with "note" as the source type.

### Cross-Browser & Responsive

- [ ] Dashboard and vault page render correctly on Chrome, Firefox, and Safari.
- [ ] Layout is usable on a 768px wide screen (tablet minimum).

### Performance Sanity Checks

- [ ] File list with 20+ files renders without lag.
- [ ] Search returns results in under 3 seconds for a vault with 50+ files.
- [ ] Flashcard generation for a 10-page PDF completes in under 30 seconds.

---

---

# PART 2 — Reusable Progress Prompt Template

---

Copy everything below the horizontal rule, fill in each `[ ]` section, and paste it at the start of a new conversation.

---

```
═══════════════════════════════════════════════════════════════
ASCRIBE — SESSION CONTEXT PROMPT
═══════════════════════════════════════════════════════════════

INSTRUCTIONS FOR THE AI
────────────────────────
You are a senior full-stack engineer helping a small team (2–3 developers)
build a web application called AScribe. Before you do anything else, read
BOTH sections below in full:

  1. The original product description (SECTION A).
  2. The current project status (SECTION B).

After reading both sections:
  - Reconcile what has been built against the original master plan.
  - If the project has drifted (different tech choices, skipped steps, changed
    architecture), acknowledge the drift and adapt your guidance to the CURRENT
    state of the project — do not blindly follow the original plan if it no
    longer applies.
  - If something is broken or blocked, diagnose it before proposing next steps.
  - Then proceed to the TASK in SECTION C.

Always assume:
  - Team size: 2–3 developers.
  - Hosting is optimized for free-tier platforms during development.
  - Redis and Celery are self-hosted Docker containers in all environments —
    there is no managed Redis service (no Upstash or similar). Redis runs
    as a container defined in docker-compose.yml and docker-compose.prod.yml.
  - The only hosted/managed external services are: Supabase (DB + auth +
    storage), Vercel (frontend), and Railway or Fly.io (container hosting).
  - Frontend uses TanStack Router for routing — not react-router-dom.
  - Frontend uses Tailwind CSS V4 (CSS-first, no tailwind.config.ts).
  - LLM is GPT-4o-nano via LangChain + OpenAI.
  - The plan may have evolved. The current state in SECTION B takes precedence
    over the original plan when they conflict.
  - Prefer practical, incremental steps over large rewrites.

═══════════════════════════════════════════════════════════════
SECTION A — ORIGINAL PRODUCT DESCRIPTION
[ Paste the full AScribe product description here. Do not edit it. ]
═══════════════════════════════════════════════════════════════

< PASTE PRODUCT DESCRIPTION HERE >

═══════════════════════════════════════════════════════════════
SECTION B — CURRENT PROJECT STATUS
[ Fill in each field honestly. Be specific. ]
═══════════════════════════════════════════════════════════════

DATE: [ e.g. 2025-11-03 ]

── What has been built and is working ──────────────────────────
[ List each completed piece. Be specific about what "working" means.
  Example:
  - Project repo created, monorepo structure in place.
  - Docker Compose runs API + Worker + Redis locally without errors.
  - Supabase project provisioned, pgvector enabled, all migrations applied.
  - Auth flow complete: Google OAuth sign-in, JWT verified on backend.
  - Vault CRUD endpoints complete and manually tested via Postman.
  - File upload endpoint works; files land in Supabase Storage.
  - Celery worker receives jobs but ingestion pipeline not yet wired.
]

< FILL IN HERE >

── What is in progress ─────────────────────────────────────────
[ What is currently being worked on but not finished? ]

< FILL IN HERE >

── What is broken or blocked ────────────────────────────────────
[ Describe any errors, failures, or blockers in detail.
  Include error messages, stack traces, or unexpected behaviors.
  Example:
  - Celery worker crashes on startup with: "ModuleNotFoundError: No module
    named 'docling'". Requirements not installed in Dockerfile.worker yet.
  - Hybrid search SQL returns zero results even when chunks are present.
    Suspect the ts_vector generated column is not being populated.
]

< FILL IN HERE >

── Decisions that deviate from the original plan ────────────────
[ Note any tech choices, architectural changes, or scope cuts made
  since the original plan. Explain why if you remember.
  Example:
  - Using Fly.io instead of Railway (Railway free tier was deprecated).
  - Replaced Docling with pypdf2 + pytesseract (Docling too heavy for
    free-tier container memory).
  - Dropped the Quiz feature for MVP scope.
  - Using TanStack Router v2 — minor API differences from plan examples.
]

< FILL IN HERE >

── Current file/folder structure (optional but helpful) ─────────
[ If the structure has diverged significantly from the plan, paste
  your actual top-level structure here. ]

< PASTE TREE OUTPUT HERE, OR LEAVE BLANK >

── Environment / infra status ───────────────────────────────────
[ Which services are provisioned and working? ]

  Supabase (dev project):     [ provisioned / not yet ]
  Supabase (prod project):    [ provisioned / not yet ]
  Redis (local Docker):       [ working / broken ]
  Redis (prod Docker):        [ deployed / not yet ]
  Vercel (frontend):          [ deployed / not yet ]
  Railway/Fly (API):          [ deployed / not yet ]
  Railway/Fly (Worker):       [ deployed / not yet ]
  Google OAuth:               [ configured / not yet ]
  OpenAI API key:             [ set / not yet ]

═══════════════════════════════════════════════════════════════
SECTION C — TODAY'S TASK OR QUESTION
[ Write what you want to accomplish or ask in this session. ]
═══════════════════════════════════════════════════════════════

< WRITE YOUR SPECIFIC TASK, QUESTION, OR PROBLEM HERE >

Examples of good tasks:
  - "Wire up the Celery ingestion pipeline end-to-end. Walk me through each
    file I need to build and the exact code for each."
  - "The hybrid search SQL is returning no results. Here is my current
    retriever.py — help me debug it."
  - "Build the VaultPage frontend component including file upload, status
    polling, and the search panel."
  - "Write the full Dockerfile, Dockerfile.worker, and docker-compose.prod.yml
    for the containerized backend deployment."
  - "Set up TanStack Router with file-based routing and the auth guard in
    __root.tsx. Show me every file I need to create."
  - "Review my current chunker.py and suggest improvements to chunk quality
    for a 200-page academic PDF."

═══════════════════════════════════════════════════════════════
END OF CONTEXT PROMPT
═══════════════════════════════════════════════════════════════
```
