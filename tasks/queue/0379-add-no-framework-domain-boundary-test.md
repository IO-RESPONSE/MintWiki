# 0379 Add no-framework-domain boundary test

## Goal

도메인 계층 프레임워크 import 금지 검사를 보강한다.

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

PHP 전환 가능성을 해치는 import를 차단한다.
