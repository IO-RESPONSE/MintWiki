# 0021 Add Document Get Service

## Goal

Add document service lookup behavior.

## Scope

- `src/modules/document/service.py`
- `tests/modules/document/test_service.py`

## Acceptance Criteria

- Service can get by id.
- Service can get by title.
- Missing document behavior is explicit and tested.

## Out of Scope

- HTTP routes.
- ACL checks.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

