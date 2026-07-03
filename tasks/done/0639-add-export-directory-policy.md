# 0639 Add export directory policy

## Goal

export directory 정책을 문서화한다.

## Phase

Phase E: Shared Hosting Packaging and Installer, 0611-0670.

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

public 밖 저장을 기본으로 한다.
