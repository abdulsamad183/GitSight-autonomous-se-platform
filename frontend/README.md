# Frontend

Next.js web application for GitSight.

## Local development

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL. Required for production builds. |
| `NEXT_PUBLIC_API_PROXY` | Set to `true` on Vercel so the browser uses same-origin `/api/*` rewrites. |

## Vercel deployment

1. Set **Root Directory** to `frontend`.
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://gitsight-api.onrender.com`)
   - `NEXT_PUBLIC_API_PROXY` = `true`
3. Deploy. API requests from the browser go to `/api/*` on Vercel and are proxied to Render.

## Scripts

```bash
npm run dev      # Development server
npm run lint     # ESLint
npm run test     # Vitest
npm run build    # Production build
```
