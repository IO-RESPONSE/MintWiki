# 0385 Add portable sorting contract

## Goal

정렬 계약을 문서화한다.

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

DB별 NULL 정렬 차이를 피한다.
