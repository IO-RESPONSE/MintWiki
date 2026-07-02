# 0621 Add installer DB form

## Goal

installer DB 설정 폼을 추가한다.

## Phase

Phase E: Shared Hosting Packaging and Installer, 0611-0670.

## Scope

- php/src/Ui

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

MariaDB DSN/user/password를 받는다.
