# 0019 Add In-Memory Document Repository

## Goal

Add an in-memory document repository for early tests.

## Scope

- `src/modules/document/repository.py`
- `tests/modules/document/test_repository.py`

## Acceptance Criteria

- Repository can create documents.
- Repository can fetch by id.
- Repository can fetch by normalized title.
- Duplicate normalized titles are rejected.

## Out of Scope

- Database persistence.
- Revision integration.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

