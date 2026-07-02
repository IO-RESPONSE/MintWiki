# 0401 Add PHP document title normalizer

## Goal

PHP 제목 정규화기를 추가한다.

## Phase

Phase B: PHP Runtime Skeleton, 0391-0440.

## Scope

- php/src/Modules/Document
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

shared fixture로 Python과 결과를 맞춘다.
