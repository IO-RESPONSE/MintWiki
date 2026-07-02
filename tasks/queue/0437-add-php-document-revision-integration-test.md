# 0437 Add PHP document revision integration test

## Goal

PHP 문서+리비전 통합 테스트를 추가한다.

## Phase

Phase B: PHP Runtime Skeleton, 0391-0440.

## Scope

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

source가 첫 리비전으로 연결되는지 검증한다.
