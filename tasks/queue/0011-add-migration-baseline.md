# 0011 Add Migration Baseline

## Goal

Add migration tool configuration and baseline directory.

## Scope

- `alembic.ini`
- `migrations/`
- `migrations/env.py`

## Acceptance Criteria

- Migration config can import app settings.
- Migration directory exists.
- No application tables are added yet.

## Out of Scope

- Creating document or revision tables.
- Running a live database migration.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

