# 0351 Document PHP replacement strategy

## Goal

PHP 전환 전략과 1:1 모듈 교체 원칙을 문서화한다.

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

Python 유지 기간, PHP 전환 기준, 금지할 결합을 명시한다.
