# 0388 Add PHP replacement readiness checklist

## Goal

PHP 전환 준비 체크리스트를 추가한다.

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

모듈별 ready/not-ready 기준을 둔다.
