# GitSight

GitSight is an open-source platform for repository-aware software engineering. Paste a public GitHub URL to analyze code structure, search indexed symbols, explore dependency graphs, chat with an LLM grounded in your codebase, generate documentation, and review pull requests.

**Status:** v0.1.0

## Key features

- **Repository analysis** — Clone a GitHub repository, parse source files with Tree-sitter, extract symbols and dependencies, and track analysis jobs with staged progress.
- **Code indexing** — Chunk source files and store 384-dimensional embeddings in PostgreSQL with pgvector for semantic retrieval.
- **Hybrid search** — Keyword, semantic, and hybrid search modes over indexed code chunks.
- **Dependency graph** — Interactive structure graph of files and imports (React Flow).
- **Repository chat** — LLM chat with RAG retrieval from indexed chunks and tool-assisted context gathering (Groq).
- **Documentation generation** — AI-generated repository documentation from analyzed code.
- **Pull request review** — LLM-powered PR reviews with diff and graph context.
- **Authentication** — Register, login, and session management via HTTP-only JWT cookies.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Flow |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.x, Alembic, Pydantic v2, asyncpg |
| Database | PostgreSQL with pgvector (Supabase in production) |
| Parsing | Tree-sitter (Python, JavaScript, TypeScript, Go, C, C++) |
| AI / LLM | Groq API |
| Embeddings | fastembed (local dev) or Google Gemini Embedding API (production) |
| Deployment | Vercel (frontend), Render (backend), Supabase (database) |

## Architecture overview

```
┌─────────────────┐     HTTP      ┌─────────────────┐     asyncpg    ┌─────────────────┐
│  Next.js (Web)  │ ────────────► │  FastAPI (API)  │ ─────────────► │ PostgreSQL      │
│  Vercel         │               │  Render         │                │ (pgvector)      │
└─────────────────┘               └─────────────────┘                └─────────────────┘
         │                                  │
         │  /api/* rewrites (production)    │  Groq API, Google Embeddings API,
         └──────────────────────────────────┘  GitHub API, Git clone
```

**Request flow:** Browser → Next.js (Vercel) → FastAPI endpoints → service layer → repository layer → PostgreSQL.

**Analysis pipeline:** Clone repo → scan files → Tree-sitter parse → extract symbols/dependencies → chunk code → generate embeddings → store in `chunk_embeddings` → enable search, chat, and PR review.

For more detail, see [docs/architecture.md](docs/architecture.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+
- PostgreSQL 16+ with the [pgvector](https://github.com/pgvector/pgvector) extension (Supabase provides this)
- API keys:
  - [Groq](https://console.groq.com/) — required for chat, documentation, and PR review
  - [GitHub](https://github.com/settings/tokens) — recommended for higher GitHub API rate limits
  - [Google AI](https://aistudio.google.com/apikey) — required in production when `EMBEDDING_PROVIDER=google`
- Docker (optional, for containerized local development)

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/abdulsamad183/GitSight-autonomous-se-platform.git
cd GitSight-autonomous-se-platform
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit both files with your values. See the [Environment variables](#environment-variables) section below.

### 3. Database

Create a PostgreSQL database with pgvector enabled, then set `DATABASE_URL` in `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gitsight
```

Run migrations:

```bash
cd backend
uv sync --extra dev
uv run alembic upgrade head
```

### 4. Install dependencies

**Backend:**

```bash
cd backend
uv sync --extra dev
```

**Frontend:**

```bash
cd frontend
npm install
```

### 5. Docker (optional)

From the repository root:

```bash
docker compose up --build
```

This starts the backend on port 8000 and the frontend on port 3000 using your `.env` files.

## Environment variables

Environment variable templates live in:

- **Backend:** [`backend/.env.example`](backend/.env.example)
- **Frontend:** [`frontend/.env.local.example`](frontend/.env.local.example)

### Backend (required for local development)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | JWT signing key (use a random 32+ character string in production) |
| `GROQ_API_KEY` | Groq API key for LLM features |

### Backend (recommended)

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token for repository cloning and PR sync |

### Frontend

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_API_PROXY` | Set to `true` on Vercel to proxy `/api/*` to the backend |

See the `.env.example` files for optional tuning variables (search weights, embedding settings, LLM models, indexing limits).

## Running the application

### Backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

API: `http://localhost:8000`  
Health: `GET /health` and `GET /health/ready`

### Frontend

```bash
cd frontend
npm run dev
```

App: `http://localhost:3000`

### Development commands

**Backend:**

```bash
cd backend
uv run pytest
uv run black app tests
uv run isort app tests
uv run flake8 app tests
```

**Frontend:**

```bash
cd frontend
npm run lint
npm test
npm run build
```

## Deployment overview

GitSight is designed to run as three services:

| Service | Platform | Notes |
|---------|----------|-------|
| Frontend | [Vercel](https://vercel.com) | Root directory: `frontend` |
| Backend API | [Render](https://render.com) | Docker web service; see `infrastructure/render.yaml` |
| Database | [Supabase](https://supabase.com) | PostgreSQL with pgvector; use the connection pooler (port 6543) |

**Production request path:** The browser calls same-origin `/api/*` on Vercel. Next.js rewrites proxy those requests to the Render backend. Auth cookies are issued on the Vercel domain.

### Deployment checklist

1. **Supabase** — Create a project and copy the async pooler `DATABASE_URL`. Enable pgvector if not already present.
2. **Render** — Deploy the backend using `infrastructure/render.yaml` or connect the repo with `backend/` as the root. Set `ENV=production`, `DATABASE_URL`, `SECRET_KEY`, `GROQ_API_KEY`, `GITHUB_TOKEN`, `CORS_ORIGINS`, `EMBEDDING_PROVIDER=google`, and `GOOGLE_API_KEY`. Migrations run via the pre-deploy command in the Render blueprint.
3. **Vercel** — Deploy `frontend/` with `NEXT_PUBLIC_API_URL` pointing to your Render backend URL and `NEXT_PUBLIC_API_PROXY=true`.
4. **Verify** — Confirm `GET /health/ready` returns 200, then register, log in, and analyze a public GitHub repository.

**CORS example for Render:**

```env
CORS_ORIGINS=["https://your-app.vercel.app","https://your-service.onrender.com"]
```

## Project structure

```text
GitSight-autonomous-se-platform/
├── backend/                 # FastAPI API (uv-managed)
│   ├── app/
│   │   ├── api/             # HTTP route handlers
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Business logic (analysis, indexing, AI, search)
│   ├── alembic/             # Database migrations
│   ├── tests/
│   └── .env.example
├── frontend/                # Next.js web application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # UI components
│   │   ├── hooks/           # React hooks
│   │   ├── services/        # API client functions
│   │   └── types/           # TypeScript types
│   └── .env.local.example
├── docs/                    # Architecture documentation
├── infrastructure/          # Deployment configs (Render blueprint)
├── .github/workflows/       # CI workflows
├── docker-compose.yml       # Local development with Docker
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Roadmap

### Completed

- [x] User authentication (register, login, JWT cookies)
- [x] Repository ingestion and multi-branch analysis
- [x] Tree-sitter AST parsing and symbol extraction
- [x] Code chunking and pgvector embeddings
- [x] Keyword, semantic, and hybrid search
- [x] Repository-aware AI chat with RAG
- [x] Documentation generation
- [x] Pull request review automation
- [x] Dependency structure graph visualization

### Planned

- [ ] Private repository support (GitHub OAuth / PAT)
- [ ] Automated bug detection
- [ ] Engineering audits and code quality reports
- [ ] Incremental re-indexing improvements
- [ ] Additional language support in Tree-sitter parser

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, coding standards, and pull request guidelines.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
