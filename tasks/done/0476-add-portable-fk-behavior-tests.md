# 0476 Add portable FK behavior tests

## Goal

FK 동작 portability 테스트를 추가한다.

## Phase

Phase C: ANSI SQL and MariaDB Portable DB Layer, 0441-0520.

## Scope

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

cascade/restrict 정책을 고정한다.
