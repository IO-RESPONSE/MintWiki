# 0431 Add root QA hook for optional PHP

## Goal

루트 QA에서 PHP QA를 선택 실행할 수 있게 한다.

## Phase

Phase B: PHP Runtime Skeleton, 0391-0440.

## Scope

- scripts/qa.sh

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

PHP 도구가 없으면 명확히 skip한다.
