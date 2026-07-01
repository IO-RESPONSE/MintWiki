# 0027 Add Revision Domain Model

## Goal

Add a lightweight domain model for document revisions.

## Scope

- `src/modules/revision/model.py`
- `tests/modules/revision/test_model.py`

## Acceptance Criteria

- Model has id, document id, source, author id, parent revision id, and summary.
- Model supports first revision with no parent.
- Tests verify construction.

## Out of Scope

- Diff.
- Persistence.
- API routes.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

