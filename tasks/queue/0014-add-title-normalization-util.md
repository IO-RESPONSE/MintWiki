# 0014 Add Title Normalization Utility

## Goal

Add the first document title normalization utility.

## Scope

- `src/modules/document/title.py`

## Acceptance Criteria

- Function trims surrounding whitespace.
- Function collapses internal whitespace to single spaces.
- Function rejects empty titles with a clear exception.
- Function does not touch database state.

## Out of Scope

- Namespace parsing.
- Redirect handling.
- API routes.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

