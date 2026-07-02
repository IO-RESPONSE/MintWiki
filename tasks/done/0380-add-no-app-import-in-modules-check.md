# 0380 Add no-app-import-in-modules check

## Goal

모듈 도메인이 app 계층을 import하지 못하게 검사한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- scripts
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

UI/API 어댑터 역참조를 차단한다.
