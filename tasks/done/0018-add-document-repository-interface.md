# 0018 Add Document Repository Interface

## Goal

Define the document repository interface.

## Scope

- `src/modules/document/repository.py`

## Acceptance Criteria

- Interface defines create, get by id, and get by normalized title methods.
- Interface is storage-agnostic.
- Type hints reference the document domain model.

## Out of Scope

- In-memory implementation.
- Database implementation.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

