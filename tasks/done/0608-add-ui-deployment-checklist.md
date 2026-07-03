# 0608 Add UI deployment checklist

## Goal

UI 배포 체크리스트를 추가한다.

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

파일 권한, cache, public path를 포함한다.
