# 0007 Add Docker Compose

## Goal

Add local Docker Compose services for app and PostgreSQL.

## Scope

- `docker-compose.yml`
- `README.md`

## Acceptance Criteria

- Compose defines `app` and `postgres` services.
- App service builds from the local Dockerfile.
- PostgreSQL has a named volume.
- README includes a local compose startup command.

## Out of Scope

- Redis service.
- Search service.
- Production deployment.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

