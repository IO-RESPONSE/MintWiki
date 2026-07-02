# 0561 Add Python UI deprecation note

## Goal

Python UI 직접 구현 보류/폐기 기준을 문서화한다.

## Phase

Phase D: Server-rendered UI after PHP and DB, 0521-0610.

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

최종 UI 기준은 PHP shared hosting으로 둔다.
