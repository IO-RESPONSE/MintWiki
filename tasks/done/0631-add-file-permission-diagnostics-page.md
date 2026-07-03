# 0631 Add file permission diagnostics page

## Goal

파일 권한 진단 페이지를 추가한다.

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

관리자 진단 화면과 연결한다.
