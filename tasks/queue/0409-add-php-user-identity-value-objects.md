# 0409 Add PHP user identity value objects

## Goal

PHP 사용자 identity value object를 추가한다.

## Phase

Phase B: PHP Runtime Skeleton, 0391-0440.

## Scope

- php/src/Modules/User

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

anonymous/user/ip identity 구분을 둔다.
