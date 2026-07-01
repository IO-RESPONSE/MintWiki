# 0024 Add Get Document API

## Goal

Add an API endpoint for fetching a document by title or id.

## Scope

- `src/modules/document/router.py`
- `tests/modules/document/test_router.py`

## Acceptance Criteria

- Endpoint can return a previously created document.
- Missing documents return a clear 404 response.
- Tests cover success and missing cases.

## Out of Scope

- Revision body rendering.
- ACL.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

