# 0028 Add In-Memory Revision Repository

## Goal

Add an in-memory revision repository for early service tests.

## Scope

- `src/modules/revision/repository.py`
- `tests/modules/revision/test_repository.py`

## Acceptance Criteria

- Repository can create revisions.
- Repository can fetch by id.
- Repository can list revisions for a document in creation order.

## Out of Scope

- Database persistence.
- Diff generation.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

