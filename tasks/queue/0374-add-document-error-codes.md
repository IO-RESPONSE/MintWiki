# 0374 Add document error codes

## Goal

document 모듈 error code 상수를 추가한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- src/modules/document
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

duplicate, not_found, empty_title 등을 고정한다.
