# 0622 Add installer DB connection test

## Goal

installer DB 연결 테스트를 추가한다.

## Phase

Phase E: Shared Hosting Packaging and Installer, 0611-0670.

## Scope

- php/src/Installer

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

실제 schema 적용 전 확인한다.
