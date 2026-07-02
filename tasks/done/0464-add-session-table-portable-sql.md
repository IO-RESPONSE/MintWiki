# 0464 Add session table portable SQL

## Goal

session table portable SQL 초안을 추가한다.

## Phase

Phase C: ANSI SQL and MariaDB Portable DB Layer, 0441-0520.

## Scope

- db/schema

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

shared hosting 파일 세션 대안은 별도다.
