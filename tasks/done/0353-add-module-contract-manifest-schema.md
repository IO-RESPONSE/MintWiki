# 0353 Add module contract manifest schema

## Goal

모듈 계약 manifest 스키마를 추가한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- docs
- src/modules

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

각 모듈의 port, service, repository, fixture 위치를 선언한다.
