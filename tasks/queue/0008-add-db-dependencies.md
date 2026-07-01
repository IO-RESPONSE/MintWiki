# 0008 Add Database Dependencies

## Goal

Add database-related Python package dependencies.

## Scope

- `pyproject.toml`

## Acceptance Criteria

- SQLAlchemy async-capable dependency is added.
- PostgreSQL driver dependency is added.
- Migration tool dependency is added.
- Existing tests still pass.

## Out of Scope

- Creating database connections.
- Creating migrations.

## QA

- `scripts/bootstrap.sh`
- `scripts/test.sh`
- `scripts/qa.sh`

