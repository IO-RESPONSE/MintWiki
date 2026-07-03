# 0616 Add local config loader

## Goal

local config loader를 추가한다.

## Phase

Phase E: Shared Hosting Packaging and Installer, 0611-0670.

## Scope

- php/src/App

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

환경변수가 없어도 파일 설정을 읽는다.
