# 0060 Add persistence phase QA checklist

## Goal

Add QA checklist for document/revision persistence.

## Phase

PostgreSQL Persistence: database-backed document and revision storage.

## Scope

- src/modules/document, src/modules/revision, migrations, tests/modules

## Acceptance Criteria

- The task implements only the behavior named in the goal.
- Relevant tests or fixtures are added or updated.
- Existing tests continue to pass.
- The change is small enough to review as one runner cycle.

## Out of Scope

- Work from later task numbers.
- Broad refactors across unrelated modules.
- Production deployment changes.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

Keep this task narrow. If implementation reveals missing prerequisite work, create a new queued task instead of expanding this one.
