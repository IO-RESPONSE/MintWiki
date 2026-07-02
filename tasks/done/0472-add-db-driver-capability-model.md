# 0472 Add DB driver capability model

## Goal

DB driver capability model을 추가한다.

## Phase

Phase C: ANSI SQL and MariaDB Portable DB Layer, 0441-0520.

## Scope

- src/persistence
- tests

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

returning/json/fulltext 지원 여부를 표현한다.
