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


═══════════════════════════════════════════════════════════════
SECTION B — CURRENT PROJECT STATUS
═══════════════════════════════════════════════════════════════

DATE: 2026-03-28

── What has been built and is working ──────────────────────────
  - Monorepo, dev tooling, and Docker scaffolding complete.
  - Frontend scaffolded (Vite + React + TypeScript, TanStack Router,
    TanStack Query, Zustand, Tailwind V4, shadcn/ui).
  - Backend scaffolded (FastAPI, async SQLAlchemy, JWT auth via Supabase
    JWKS, Pydantic settings).
  - Database schema live on Supabase dev (vaults, files, chunks with
    pgvector, indexes, triggers, RLS). NOTE: notes table migration not
    yet applied — Note model must not be used until it is.
  - Google OAuth configured for dev.
  - ORM models and Pydantic schemas for Vault and File. Chunk schemas
    intentionally omitted (pipeline-internal).
  - Celery ingestion worker complete: full extract → clean → chunk →
    embed → insert pipeline with idempotent retries and FAILED status
    on non-retryable errors.
  - Unit and integration tests written and passing for all of the above.
  - Full pipeline layer: embedder.py (BGE singleton, asymmetric prefix on
    queries only) and retriever.py (RRF hybrid SQL via sqlalchemy.text).
  - Full service layer: vault_service, file_service, search_service,
    ai_service. Commit/flush split: services flush, routes commit.
    Supabase storage wrapped in asyncio.to_thread.
  - Full API route layer: vaults, files, search, ai — all wired into
    main.py under /api/v1. AI routes guarded by vault_has_ready_files
    (422 if no indexed content). Upload returns 202.
  - Schema layer extended: schemas/search.py and schemas/ai.py added.
    QuizQuestion.explanation is list[str] (one per option). Pydantic
    validators enforce option label format and explanation length.
  - Shared Supabase dependency: app/core/clients.py, get_supabase()
    lru_cache singleton using service role key.
  - Unit test suite complete: tests/unit/ with conftest, fixtures
    (mock_db, mock_supabase, app, client, make_vault, make_file) and
    full coverage for all services and routes. __init__.py files present
    in all test subdirectories.

── What is in progress ─────────────────────────────────────────

  < FILL IN HERE >

── What is broken or blocked ────────────────────────────────────

  none

── Current file/folder structure (optional but helpful) ─────────

  ascribe/
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   │   └── v1/
  │   │   │       ├── vaults.py
  │   │   │       ├── files.py
  │   │   │       ├── search.py
  │   │   │       └── ai.py
  │   │   ├── core/
  │   │   │   ├── config.py
  │   │   │   ├── database.py
  │   │   │   ├── security.py
  │   │   │   └── clients.py
  │   │   ├── models/
  │   │   │   ├── __init__.py
  │   │   │   ├── vault.py
  │   │   │   ├── file.py
  │   │   │   └── chunk.py
  │   │   ├── schemas/
  │   │   │   ├── vault.py
  │   │   │   ├── file.py
  │   │   │   ├── search.py
  │   │   │   └── ai.py
  │   │   ├── services/
  │   │   │   ├── vault_service.py
  │   │   │   ├── file_service.py
  │   │   │   ├── search_service.py
  │   │   │   └── ai_service.py
  │   │   ├── workers/
  │   │   │   ├── celery_app.py
  │   │   │   └── ingestion.py
  │   │   ├── pipeline/
  │   │   │   ├── embedder.py
  │   │   │   └── retriever.py
  │   │   ├── enums.py
  │   │   └── main.py
  │   ├── migrations/
  │   │   └── versions/
  │   │       └── c1a..._init_schema.py   # applied
  │   ├── tests/
  │   │   ├── conftest.py
  │   │   ├── unit/
  │   │   │   ├── __init__.py
  │   │   │   ├── conftest.py
  │   │   │   ├── services/
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── test_vault_service.py
  │   │   │   │   ├── test_file_service.py
  │   │   │   │   ├── test_search_service.py
  │   │   │   │   └── test_ai_service.py
  │   │   │   └── routes/
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── test_vaults_route.py
  │   │   │   │   ├── test_files_route.py
  │   │   │   │   ├── test_search_route.py
  │   │   │   │   └── test_ai_route.py
  │   │   │   ├── test_celery_app.py
  │   │   │   └── test_ingestion.py
  │   │   └── integration/
  │   │       ├── conftest.py
  │   │       ├── test_supabase_connectivity.py
  │   │       └── test_ingestion_pipeline.py
  │   ├── Dockerfile
  │   ├── Dockerfile.worker
  │   ├── requirements.txt
  │   ├── ruff.toml
  │   └── alembic.ini
  ├── frontend/
  │   ├── src/
  │   │   ├── api/
  │   │   ├── components/
  │   │   ├── pages/
  │   │   ├── routes/
  │   │   ├── stores/
  │   │   ├── hooks/
  │   │   ├── types/
  │   │   └── main.tsx
  │   ├── index.html
  │   ├── vite.config.ts
  │   └── package.json
  ├── docker-compose.yml
  ├── .env.example
  └── README.md


── Environment / infra status ───────────────────────────────────

  Supabase (dev project):   provisioned
  Supabase (prod project):  not yet
  Redis (local Docker):     not yet verified end-to-end
  Redis (prod Docker):      not yet
  Vercel (frontend):        not yet
  Railway/Fly (API):        not yet
  Railway/Fly (Worker):     not yet
  Google OAuth:             configured (dev)
  OpenAI API key:           not yet

═══════════════════════════════════════════════════════════════
SECTION C — TODAY'S TASK OR QUESTION
═══════════════════════════════════════════════════════════════

< WRITE YOUR SPECIFIC TASK, QUESTION, OR PROBLEM HERE >

═══════════════════════════════════════════════════════════════
END OF CONTEXT PROMPT
═══════════════════════════════════════════════════════════════
