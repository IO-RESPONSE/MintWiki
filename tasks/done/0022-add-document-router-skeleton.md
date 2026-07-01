# 0022 Add Document Router Skeleton

## Goal

Add a document API router skeleton and register it with the app.

## Scope

- `src/modules/document/router.py`
- `src/app/main.py`
- `tests/test_routes.py`

## Acceptance Criteria

- App registers a document router under `/api/documents`.
- Router import does not create storage state at import time.
- Tests verify route registration.

## Out of Scope

- Create/get endpoint implementation.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

