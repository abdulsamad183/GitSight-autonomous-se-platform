# GitSight — Autonomous Software Engineering Platform

AI-powered platform for repository-aware software engineering: code search, documentation, PR review, and engineering insights.

**Status:** Foundation release (v0.1.0)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, TailwindCSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.x, Alembic, Pydantic v2 |
| Database | Supabase PostgreSQL |
| AI | Groq API |
| Deployment | Vercel (frontend), Render (backend), Supabase (database) |

## Project Structure

```text
GitSight-autonomous-se-platform/
├── frontend/          # Next.js web application
├── backend/           # FastAPI API (uv-managed)
├── docs/              # Architecture and design docs
├── infrastructure/    # Deployment configs (Render, etc.)
├── .github/           # CI workflows
├── docker-compose.yml # Local dev (backend + frontend)
└── README.md
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+
- Supabase project with PostgreSQL connection string
- Docker (optional, for containerized local dev)

## Setup

### 1. Clone and configure environment

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL, SECRET_KEY, and GROQ_API_KEY

# Frontend
cp frontend/.env.local.example frontend/.env.local
```

**Supabase `DATABASE_URL` (async):**

```env
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

**Frontend local dev:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_PROXY=false
```

### 2. Backend

```bash
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:3000`

### 4. Docker (optional)

```bash
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/health/ready` | Readiness check (includes database) |
| GET | `/api/v1/version` | Service version |

## Development

### Backend

```bash
cd backend
uv run pytest
uv run black app tests
uv run isort app tests
uv run flake8 app tests
```

### Frontend

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Production deployment

### Architecture

The browser talks to the Vercel frontend at same-origin `/api/*`. Next.js rewrites proxy those requests to the Render backend. Auth cookies are set on the Vercel domain.

### Checklist

| Platform | Required configuration |
|----------|------------------------|
| **Supabase** | `DATABASE_URL` using the pooler (port 6543). Add `?sslmode=require` if needed. |
| **Render** | `ENV=production`, `DATABASE_URL`, `SECRET_KEY` (32+ chars), `GROQ_API_KEY`, `GITHUB_TOKEN`, `CORS_ORIGINS`. Migrations run via `preDeployCommand` in `infrastructure/render.yaml`. |
| **Vercel** | Root directory: `frontend`. `NEXT_PUBLIC_API_URL` = Render backend URL. `NEXT_PUBLIC_API_PROXY=true`. |

**Render `CORS_ORIGINS` example:**

```env
CORS_ORIGINS=["https://your-app.vercel.app","https://your-service.onrender.com"]
```

**Render plan note:** Set `EMBEDDING_PROVIDER=google` and `GOOGLE_API_KEY` so embeddings run via the Gemini API (no local model RAM). See `infrastructure/render.yaml`.

### Deploy steps

1. Create Supabase project and copy the async pooler `DATABASE_URL`.
2. Deploy backend from `infrastructure/render.yaml` (or connect the repo with root `backend/`).
3. Set Render environment variables and confirm `/health/ready` returns 200.
4. Deploy `frontend/` to Vercel with proxy env vars pointing at the Render URL.
5. Smoke test: register, login, analyze a public GitHub repository.

## Roadmap

- [x] User authentication (register, login, JWT)
- [x] Repository ingestion
- [x] AST parsing and code indexing
- [x] Embeddings and semantic search
- [x] Repository-aware AI chat
- [x] Documentation generation
- [x] PR review automation
- [ ] Private repository support (GitHub OAuth / PAT)
- [ ] Bug detection
- [ ] Engineering audits

## License

Proprietary — All rights reserved.
