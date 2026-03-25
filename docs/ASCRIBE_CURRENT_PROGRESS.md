
# Reusable Progress Prompt Template

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

# **AScribe – Personal Knowledge Intelligence System**

## Overview

AScribe is a lightweight, AI-powered knowledge management web application designed for students who want to transform their study materials into an intelligent, queryable knowledge base.

Users can upload a wide range of files—including PDFs, images, and handwritten notes—into personalized Vaults, where content is automatically processed, indexed, and made accessible through retrieval-augmented generation (RAG).

The platform enables users to search, summarize, and generate learning materials such as flashcards and quizzes, all grounded strictly in their own uploaded content—turning passive notes into an active learning system.

---

## Core Features

### 1. Vault-Wide Hybrid Search

- Combines semantic + keyword search
- Returns:
    - Relevant text fragments
    - Source references (file + location)
- Enables fast navigation across large study materials

### 2. AI Summarization

- Summarizes:
    - Entire vaults
    - Selected documents
    - Retrieved context
- Uses RAG to ensure summaries are grounded in user data

### 3. Question & Answer Generation (Flashcards + Quizzes)

- Generates:
    - Conceptual questions
    - Recall-based flashcards
    - Practice quizzes
- Uses full-context retrieval instead of isolated chunks for better coherence

### 4. Personal Notes Integration

- Users can create notes inside the vault
- Notes can be ingested into the knowledge base
- Enables blending of:
    - Uploaded materials
    - Personal understanding

### 5. File Ingestion & Storage

Supports:

- PDFs
- Images
- DOCX
- TXT
- Handwritten notes (via OCR)
- Files stored in object storage (Supabase Storage)
- Text extracted and indexed for retrieval

### 6. Future: Conversational Interface

- Chat with your Vault
- Context-aware answers using RAG
- Maintains strict grounding in user-provided data

---

## System Architecture (RAG Pipeline)

### High-Level Flow

```
[User Upload]
      ↓
[File Storage (Supabase Storage)]
      ↓
[File metadata record inserted into PostgreSQL → files table]
      ↓
[Docling – OCR + Text Extraction]
      ↓
[Text Cleaning]
      ↓
[Chunking Strategy]
      ↓
[Embedding Generation (bge-small-en-v1.5 – local, loaded in Celery worker)]
      ↓
[Chunk records + vectors inserted into PostgreSQL → chunks table (pgvector)]
      ↓
[File status updated to "ready" in PostgreSQL → files table]
```

### Query Flow (Search / Q&A / Summarization)

```
[User Query]
      ↓
[Query embedded locally (bge-small-en-v1.5 in worker)]
      ↓
[Hybrid Search Layer]
 (Keyword (tsvector) + Vector Search (pgvector) joined against chunks table)
      ↓
[Top-K Relevant Chunks]
 (each chunk carries file_id → JOIN files table for source metadata)
      ↓
[Context Assembler]
 (merge chunks OR expand to full docs depending on task)
      ↓
[LLM Prompt (GPT-4o-mini)]
      ↓
[Generated Output + Source References (filename, page, vault)]
```

### Background Job Flow (File Ingestion)

```
[API receives uploaded file]
      ↓
[File saved to Supabase Storage]
      ↓
[File metadata written to PostgreSQL → files table (status: "processing")]
      ↓
[Celery task enqueued via Redis]
      ↓
[Worker: Docling extracts text + page/section structure]
      ↓
[Worker: Text cleaned + chunked]
      ↓
[Worker: bge-small-en-v1.5 loaded (singleton, warm on worker start)]
      ↓
[Worker: Embeddings generated locally – zero API cost]
      ↓
[Worker: Chunk records + vectors bulk-inserted into chunks table]
      ↓
[Worker: files table status updated to "ready"]
      ↓
[Job complete – vault updated]
```

## Tech Stack (Cost-Efficient + Practical)

### Frontend

- React + TypeScript + Vite
- TailwindCSS + shadcn/ui (accessible component primitives, no imposed design system)
- TanStack Query v5 (modern rename of React Query – data fetching + caching)
- Zustand (state management)

### Backend

- FastAPI (Python 3.12+)
- Pydantic v2 (validation)
- Async endpoints for performance
- Celery + Redis (background job queue for file ingestion – keeps API non-blocking)

### AI / ML Pipeline

#### OCR & Document Extraction

- **Docling** (IBM, open source) – single library handling PDFs, DOCX, images, and handwritten notes with significantly better accuracy than raw Tesseract; purpose-built for RAG pipelines

#### Embeddings

- **bge-small-en-v1.5** (BAAI, open source) – 130MB model downloaded once and loaded as a singleton inside the Celery worker at startup; zero API cost, 384-dimension output, best quality-to-size ratio among local embedding models; served via the `sentence-transformers` Python library

#### LLM

- **GPT-4o-mini** – cost-efficient, strong reasoning, sufficient for summarization, Q&A, and flashcard generation

#### RAG Orchestration

- **LangChain** – industry-standard framework for wiring together chunking, retrieval, context assembly, and prompting

### Storage

#### Files

- **Supabase Storage** – replaces AWS S3; generous free tier, integrated with the same Supabase project as the database and auth

#### Database

- **Supabase (PostgreSQL + pgvector)** – replaces standalone PostgreSQL setup; pgvector extension built-in; one dashboard, one service
- Stores all file metadata, chunk records, vault structure, and user notes in a structured relational schema (see PostgreSQL Schema in Architecture section)
- pgvector `HNSW` index on the `chunks.embedding` column for fast approximate nearest-neighbour search
- PostgreSQL `tsvector` generated column on `chunks.content` for native full-text keyword search — no additional search infrastructure needed

#### Cache / Queue

- **Redis** – Celery broker and result backend for background ingestion jobs

### Authentication

- **Supabase Auth** – replaces custom OAuth + JWT implementation; handles Google login, session management, and JWT issuance out of the box; saves significant boilerplate

### DevOps

#### Local Development

- **Docker Compose** – orchestrates FastAPI backend, Celery worker, and Redis locally

#### Deployment

- **Vercel** – frontend hosting (free tier, automatic preview deployments on every PR)
- **Railway or Fly.io** – backend hosting (supports containerized FastAPI + Celery + Redis, free tier available)

#### CI/CD

- **GitHub Actions** – automated pipeline for linting, testing, and deployment on push

---

## Architecture Notes

### Why bge-small-en-v1.5 over OpenAI embeddings

bge-small-en-v1.5 (released by BAAI) consistently ranks among the top small embedding models on the MTEB benchmark. At 130MB it downloads once, lives on disk, and is loaded as a singleton when the Celery worker process starts — meaning subsequent ingestion jobs reuse the warm model with no cold-start penalty and zero per-call API cost. The `sentence-transformers` library makes loading and inference a two-line operation. The 384-dimension output is natively supported by pgvector and keeps index size small for a local or free-tier deployment.

### Why PostgreSQL for file metadata (not just vectors)

Every file needs structured metadata — original filename, upload status, page count, vault association, file type — that is queried relationally, not semantically. Storing this in the same PostgreSQL instance as the vectors means a single JOIN between `files` and `chunks` can return a search result with full source attribution in one query. It also means file status tracking (processing → ready → failed), vault-scoped file listings, and note ingestion state are all handled by the same database with ACID guarantees — no second data store needed.

### Why Supabase over separate services

At small scale, Supabase consolidates file storage (S3-equivalent), PostgreSQL with pgvector, and authentication into a single managed service with a unified dashboard and free tier. This reduces operational overhead significantly and lets the focus remain on the RAG pipeline and AI features rather than infrastructure wiring.

### Why Celery + Redis

File ingestion (OCR → chunking → embedding) is slow and should never block the API response. Celery offloads this work to a background worker process. Redis serves as the message broker. This pattern mirrors production-grade systems and is worth demonstrating on a resume.

### Why Docling over Tesseract

Tesseract requires significant post-processing pipelines to extract clean, structured text from PDFs and mixed documents. Docling handles layout-aware extraction across all supported file types in a single call, outputs clean markdown-ready text, and is specifically optimised for downstream RAG use.

### Why TanStack Query over raw React Query

TanStack Query v5 is the direct successor and rebranded version of React Query. The API is cleaner, TypeScript support is first-class, and it is the current industry standard for async data management in React applications.

### Why shadcn/ui

shadcn/ui components are copy-pasted into your project rather than installed as a dependency. This gives full ownership over the component code, keeps the bundle lean, and results in a polished, accessible UI without enforcing a design system — ideal for a resume project where design quality matters.


═══════════════════════════════════════════════════════════════
SECTION B — CURRENT PROJECT STATUS
[ Fill in each field honestly. Be specific. ]
═══════════════════════════════════════════════════════════════

DATE: 2026-03-25

── What has been built and is working ──────────────────────────
  - Monorepo structure in place (backend/, frontend/, docker-compose.yml,
    .env.example, README.md).
  - Development tooling configured: Ruff (backend linting/formatting),
    ESLint + Prettier (frontend), pre-commit hooks wired and working.
  - Frontend scaffolded with Vite + React + TypeScript. TanStack Router,
    TanStack Query, Zustand, Axios installed. Tailwind CSS V4 configured
    via @tailwindcss/vite plugin (no tailwind.config.ts). shadcn/ui
    initialized.
  - Backend Python environment set up with all dependencies in
    requirements.txt. FastAPI, SQLAlchemy asyncpg, Alembic, Celery,
    sentence-transformers, docling, langchain-openai, supabase-py,
    pgvector all installed.
  - Supabase dev project provisioned. uuid-ossp and pgvector extensions
    enabled. Full schema applied via Alembic migration (vaults, files,
    chunks tables with all indexes, triggers, and RLS policies).
    NOTE: notes table is NOT yet in the database — model exists in code
    but must not be used until its migration is applied.
  - Google OAuth configured: Supabase Auth provider set up with Google
    Client ID and Secret. Localhost redirect URI registered in Google
    Cloud Console.
  - Backend core foundation built:
      - app/core/config.py — Pydantic BaseSettings singleton reading
        all env vars from .env.
      - app/core/database.py — Async SQLAlchemy engine + session factory
        + DeclarativeBase. get_db dependency ready for route injection.
      - app/core/security.py — JWT verification against Supabase JWKS
        endpoint. get_current_user FastAPI dependency implemented.
      - app/main.py — FastAPI app factory with CORS middleware,
        /health endpoint, and api_router mounted at /api/v1.
  - ORM models defined for all four tables:
      - app/models/vault.py — Vault model with metadata JSONB column.
      - app/models/file.py — File model with total_chunks, total_tokens,
        metadata columns. storage_path intentionally excluded from schema.
      - app/models/chunk.py — Chunk model with ts_vector mapped as
        Computed(..., persisted=True) so SQLAlchemy never writes to the
        DB-generated column. importance_score and metadata included.
      - app/models/note.py — Model defined but guarded with a warning
        comment; must not be imported until notes migration is applied.
  - Pydantic schemas defined:
      - app/schemas/vault.py — VaultCreate, VaultUpdate, VaultResponse,
        VaultListResponse.
      - app/schemas/file.py — FileResponse, FileListResponse. No
        FileCreate (upload is multipart, not JSON). No FileUpdate (file
        rows are only mutated by the worker, not the client).
      - Chunk schemas intentionally omitted — chunks are internal to the
        RAG pipeline and never serialized to the frontend.


── What is in progress ─────────────────────────────────────────

< FILL IN HERE >

── What is broken or blocked ────────────────────────────────────

< FILL IN HERE >

── Current file/folder structure (optional but helpful) ─────────

  ascribe/
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   │   └── v1/
  │   │   │       ├── __init__.py       # api_router, mounts sub-routers
  │   │   │       └── vaults.py         # Vaults CRUD endpoints
  │   │   ├── core/
  │   │   │   ├── config.py
  │   │   │   ├── database.py
  │   │   │   └── security.py
  │   │   ├── models/
  │   │   │   ├── __init__.py
  │   │   │   ├── vault.py
  │   │   │   ├── file.py
  │   │   │   └── chunk.py
  │   │   ├── schemas/
  │   │   │   ├── vault.py
  │   │   │   └── file.py
  │   │   ├── services/                 # empty, not yet built
  │   │   ├── workers/                  # empty, not yet built
  │   │   ├── pipeline/                 # empty, not yet built
  |   |   ├── enums.py
  │   │   └── main.py
  │   ├── migrations/
  │   │   └── versions/
  │   │       └── c1a1995a14ac_init_schema.py   # applied
  │   ├── tests
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
[ Which services are provisioned and working? ]

  Supabase (dev project):   provisioned
  Supabase (prod project):  not yet
  Redis (local Docker):     not yet verified (docker-compose.yml written
                            but not smoke-tested end-to-end)
  Redis (prod Docker):      not yet
  Vercel (frontend):        not yet
  Railway/Fly (API):        not yet
  Railway/Fly (Worker):     not yet
  Google OAuth:             configured (dev)
  OpenAI API key:           not yet

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
