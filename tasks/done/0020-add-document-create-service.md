# 0020 Add Document Create Service

## Goal

Add document service logic for creating a document.

## Scope

- `src/modules/document/service.py`
- `tests/modules/document/test_service.py`

## Acceptance Criteria

- Service normalizes the title.
- Service delegates storage to repository interface.
- Duplicate title behavior is tested.

## Out of Scope

- Revision creation.
- API routes.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

