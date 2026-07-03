# 0569 Add PHP UI duplicate submit protection

## Goal

문서 폼 중복 제출 방지를 추가한다.

## Phase

Phase D: Server-rendered UI after PHP and DB, 0521-0610.

## Scope

- php/src/Security
- php/tests

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

idempotency key 또는 one-time token을 둔다.
