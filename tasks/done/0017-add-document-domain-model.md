# 0017 Add Document Domain Model

## Goal

Add a lightweight domain model for documents.

## Scope

- `src/modules/document/model.py`
- `tests/modules/document/test_model.py`

## Acceptance Criteria

- Model has id, title, normalized title, and current revision id fields.
- Model can represent a document without a current revision.
- Tests verify construction.

## Out of Scope

- SQLAlchemy mapping.
- Persistence.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

