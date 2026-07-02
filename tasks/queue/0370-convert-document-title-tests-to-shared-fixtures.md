# 0370 Convert document title tests to shared fixtures

## Goal

문서 제목 정규화 테스트를 공용 fixture 기반으로 보강한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- tests/modules/document

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

PHP가 같은 fixture를 재사용할 수 있게 한다.
