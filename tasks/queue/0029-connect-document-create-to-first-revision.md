# 0029 Connect Document Create To First Revision

## Goal

Connect document creation to creation of an initial revision.

## Scope

- `src/modules/document/service.py`
- `src/modules/revision/`
- `tests/modules/document/test_service.py`

## Acceptance Criteria

- Creating a document with source creates a first revision.
- Document current revision id is set.
- Tests verify the linked document and revision ids.

## Out of Scope

- API response expansion.
- Database transactions.
- ACL.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

