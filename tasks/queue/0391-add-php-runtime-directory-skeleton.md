# 0391 Add PHP runtime directory skeleton

## Goal

PHP 런타임 기본 디렉터리를 추가한다.

## Phase

Phase B: PHP Runtime Skeleton, 0391-0440.

## Scope

- php

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

`php/src`, `php/public`, `php/tests` 골격만 추가한다.
