# Architecture

## Overview

GitSight is an AI-powered Autonomous Software Engineering Platform. This document describes the foundation architecture.

## System Diagram

```
┌─────────────────┐     HTTP      ┌─────────────────┐     asyncpg    ┌─────────────────┐
│  Next.js (Web)  │ ────────────► │  FastAPI (API)  │ ─────────────► │ Supabase (PG)   │
│  Vercel         │               │  Render         │                │                 │
└─────────────────┘               └─────────────────┘                └─────────────────┘
```

## Backend Layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `app/api/v1/endpoints/` | HTTP route handlers |
| Services | `app/services/` | Business logic |
| Repositories | `app/repositories/` | Data access |
| Models | `app/models/` | SQLAlchemy ORM models |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Core | `app/core/` | Config, database, security, logging |

## Dependency Flow

```
Request → Middleware → Endpoint → Service → Repository → Database
```

## Future Capabilities

- Repository ingestion and AST parsing
- Embeddings and semantic code search
- Repository-aware AI chat (Groq)
- Documentation generation
- PR review and bug detection
- Architecture visualization and engineering audits
