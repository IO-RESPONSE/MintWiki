# 0577 Add PHP UI cache header policy

## Goal

UI cache header 정책을 추가한다.

## Phase

Phase D: Server-rendered UI after PHP and DB, 0521-0610.

## Scope

- docs
- php/src/Http

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

HTML과 static asset을 구분한다.
