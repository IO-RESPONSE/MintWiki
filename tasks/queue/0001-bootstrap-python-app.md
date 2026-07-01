# 0001 Bootstrap Python App

## Goal

Create the minimal Python application package and a health check route.

## Scope

- `src/app/main.py`
- `src/app/config.py`
- `tests/test_health.py`
- project dependency metadata

## Acceptance Criteria

- The app exposes `GET /health`.
- The response includes `status: ok`.
- The test suite can run locally.
- `scripts/test.sh` exits successfully.

## Out of Scope

- Database connections.
- Docker Compose.
- Authentication.
- Wiki document behavior.

## QA

- `scripts/test.sh`

## Notes

Use FastAPI unless the project direction changes before this task starts.
