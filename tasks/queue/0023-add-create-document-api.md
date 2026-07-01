# 0023 Add Create Document API

## Goal

Add an API endpoint for creating a document using the in-memory service.

## Scope

- `src/modules/document/schema.py`
- `src/modules/document/router.py`
- `tests/modules/document/test_router.py`

## Acceptance Criteria

- Endpoint accepts title and source fields.
- Endpoint returns document id and title.
- Tests verify successful create behavior.

## Out of Scope

- Revision persistence.
- Auth and ACL.
- Database persistence.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

