# 0012 Add Empty Initial Migration

## Goal

Add an initial empty migration as the migration chain root.

## Scope

- `migrations/versions/`

## Acceptance Criteria

- Migration has a stable revision id.
- Upgrade and downgrade functions exist.
- Migration does not create tables.

## Out of Scope

- Document/revision schema.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

