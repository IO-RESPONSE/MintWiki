# 0521 Add UI architecture after PHP docs

## Goal

PHP/DB 이후 UI 아키텍처를 문서화한다.

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

서버 렌더링, 정적 CSS/JS, no-build 기본을 둔다.
