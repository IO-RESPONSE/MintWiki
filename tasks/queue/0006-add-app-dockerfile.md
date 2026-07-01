# 0006 Add App Dockerfile

## Goal

Add a minimal Dockerfile for the application.

## Scope

- `Dockerfile`
- `.dockerignore`

## Acceptance Criteria

- Dockerfile uses Python 3.12.
- Dockerfile installs the project with dev dependencies acceptable for local use.
- Default command starts uvicorn for `app.main:app`.
- `.dockerignore` excludes `.venv`, git metadata, and caches.

## Out of Scope

- Docker Compose.
- Production hardening.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

