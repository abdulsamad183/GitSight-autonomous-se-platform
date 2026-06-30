# Contributing to GitSight

Thank you for your interest in contributing. This document explains how to set up a development environment, follow project conventions, and submit changes.

## Getting started

### Fork and clone

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/GitSight-autonomous-se-platform.git
cd GitSight-autonomous-se-platform
```

3. Add the upstream remote:

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/GitSight-autonomous-se-platform.git
```

4. Configure environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

5. Follow the setup steps in [README.md](README.md) to install dependencies, run migrations, and start the backend and frontend.

## Branch naming

Create a feature branch from the latest `main`:

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `test/` | Test additions or fixes |
| `refactor/` | Code restructuring without behavior change |
| `chore/` | Tooling, dependencies, or maintenance |

Examples: `feat/hybrid-search-tuning`, `fix/embedding-dimension-mismatch`, `docs/deployment-guide`

## Development workflow

1. Sync with upstream before starting work:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

2. Create your branch:

```bash
git checkout -b feat/your-feature-name
```

3. Make focused changes. Keep pull requests scoped to a single concern when possible.

4. Run tests and linters locally before pushing (see [Coding standards](#coding-standards)).

5. Push to your fork and open a pull request against `main`.

## Coding standards

### Backend (Python)

- Python 3.11
- Format with [Black](https://black.readthedocs.io/)
- Sort imports with [isort](https://pycqa.github.io/isort/)
- Lint with [flake8](https://flake8.pycqa.org/)
- Type hints where the surrounding code uses them
- Follow existing patterns in `app/api`, `app/services`, `app/repositories`, and `app/models`

```bash
cd backend
uv run black app tests
uv run isort app tests
uv run flake8 app tests
uv run pytest
```

### Frontend (TypeScript / React)

- TypeScript strict mode
- ESLint for linting
- Prettier for formatting
- Follow existing component and hook patterns in `frontend/src`

```bash
cd frontend
npm run lint
npm test
npm run build
```

### General guidelines

- Match the style and structure of the file you are editing.
- Prefer small, readable functions over large abstractions.
- Add or update tests when changing behavior.
- Do not commit secrets, API keys, or real credentials.
- Do not commit `.env` or `.env.local` files.

## Commit message guidelines

Write clear, imperative commit messages:

```
<type>: <short summary>

Optional longer description explaining why the change was made.
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

**Examples:**

```
feat: add hybrid search weight configuration

fix: truncate Google embeddings to match pgvector column size

docs: expand deployment section in README

test: cover embedding provider dimension normalization
```

Keep the subject line under 72 characters. Reference issue numbers in the body when applicable (`Fixes #123`).

## Submitting pull requests

1. Ensure your branch is up to date with `upstream/main`.
2. Push your branch to your fork.
3. Open a pull request against the `main` branch of the upstream repository.
4. Fill in the PR description:
   - **Summary** — What changed and why
   - **Test plan** — Commands run and manual steps taken
5. CI must pass:
   - Backend CI runs on changes under `backend/`
   - Frontend CI runs on changes under `frontend/`

### Pull request checklist

- [ ] Tests pass locally
- [ ] Linters pass locally
- [ ] No secrets or credentials in the diff
- [ ] Documentation updated if behavior or setup changed
- [ ] Migrations included if database schema changed

## Review expectations

- Maintainers review PRs for correctness, test coverage, and consistency with existing code.
- Address review feedback with additional commits or amendments on your branch.
- PRs may be squashed on merge.
- Large changes may be asked to split into smaller PRs.
- Be respectful and constructive in review discussions.

## Reporting issues

When filing a bug report, include:

- Steps to reproduce
- Expected vs. actual behavior
- Relevant logs or error messages (redact secrets)
- Environment (OS, Python/Node versions, deployment platform if applicable)

## Questions

Open a GitHub issue for questions about architecture, setup, or contribution scope.
