# 0364 Add admin module contract manifest

## Goal

admin 모듈 계약 manifest를 추가한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- src/modules/admin

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

관리자 액션은 audit hook을 통과해야 함을 명시한다.
