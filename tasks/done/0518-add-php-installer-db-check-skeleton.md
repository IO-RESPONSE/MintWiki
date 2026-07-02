# 0518 Add PHP installer DB check skeleton

## Goal

PHP installer DB check skeleton을 추가한다.

## Phase

Phase C: ANSI SQL and MariaDB Portable DB Layer, 0441-0520.

## Scope

- php/src/Installer

## Acceptance Criteria

- The task implements only the behavior named in the goal.
- Relevant tests or fixtures are added or updated.
- Existing tests continue to pass.
- The change is small enough to review as one runner cycle.

## Out of Scope

- Work from later task numbers.
- Broad refactors across unrelated modules.
- Production deployment changes unless explicitly named in this task.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

접속/charset/schema version 확인만 둔다.
