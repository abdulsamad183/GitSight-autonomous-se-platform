# GitSight — Autonomous Software Engineering Platform

AI-powered platform for repository-aware software engineering: code search, documentation, PR review, bug detection, and engineering audits.

**Status:** Foundation release (v0.1.0)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, TailwindCSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.x, Alembic, Pydantic v2 |
| Database | Supabase PostgreSQL |
| AI (future) | Groq API |
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
# Edit backend/.env — set DATABASE_URL and SECRET_KEY

# Frontend
cp frontend/.env.local.example frontend/.env.local
```

**Supabase `DATABASE_URL` (async):**
```env
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
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
| GET | `/health` | Health check |
| GET | `/api/v1/version` | Service version |

## Development

### Backend

```bash
cd backend
uv run pytest                    # Run tests
uv run black app tests           # Format
uv run isort app tests           # Sort imports
uv run flake8 app tests          # Lint
uv add <package>                 # Add dependency
```

### Frontend

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Deployment

- **Frontend:** Deploy `frontend/` to Vercel
- **Backend:** Deploy `backend/` to Render (see `infrastructure/render.yaml`)
- **Database:** Supabase PostgreSQL (cloud)

## Roadmap

- [ ] User authentication (register, login, JWT)
- [ ] Repository ingestion
- [ ] AST parsing and code indexing
- [ ] Embeddings and semantic search
- [ ] Repository-aware AI chat
- [ ] Documentation generation
- [ ] PR review automation
- [ ] Bug detection
- [ ] Architecture visualization
- [ ] Engineering audits

## License

Proprietary — All rights reserved.
