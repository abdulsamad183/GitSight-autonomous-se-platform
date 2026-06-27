# Backend

FastAPI backend for the GitSight Autonomous Software Engineering Platform.

Managed with [uv](https://docs.astral.sh/uv/).

## Local development

```bash
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Environment variables

See `.env.example` for the full list. Production requires:

- `ENV=production`
- `DATABASE_URL` (Supabase pooler, not localhost)
- `SECRET_KEY` (32+ character random string)
- `GROQ_API_KEY`
- `GITHUB_TOKEN` (recommended for GitHub API rate limits)
- `CORS_ORIGINS` (JSON array or comma-separated origins)

## Render deployment

Use `infrastructure/render.yaml` or deploy the `backend/Dockerfile` as a Docker web service.

- Health check path: `/health/ready`
- Pre-deploy: `uv run alembic upgrade head`
- Recommended plan: Starter or higher for heavy concurrent indexing; embeddings use ONNX (`fastembed`) and are tuned for low RAM via `EMBEDDING_BATCH_SIZE=8` and `EMBEDDING_THREADS=1` in `render.yaml`.

## Scripts

```bash
uv run pytest
uv run black app tests
uv run isort app tests
uv run flake8 app tests
```
