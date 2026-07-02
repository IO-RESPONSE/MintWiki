# 0373 Add portable exception code policy

## Goal

예외 메시지 대신 안정적인 error code 정책을 문서화한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- docs

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

PHP와 Python이 같은 code를 반환하게 한다.
