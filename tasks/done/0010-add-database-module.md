# 0010 Add Database Module

## Goal

Add a shared database module with engine/session factory placeholders.

## Scope

- `src/app/database.py`
- `tests/test_database.py`

## Acceptance Criteria

- Module exposes a function to build an engine from settings.
- Module exposes a session factory function.
- Tests verify the functions can be imported and configured.

## Out of Scope

- Real migrations.
- Document tables.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

