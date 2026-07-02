# 0541 Apply CSRF to PHP document forms

## Goal

PHP 문서 폼에 CSRF를 적용한다.

## Phase

Phase D: Server-rendered UI after PHP and DB, 0521-0610.

## Scope

- php/src/Ui
- php/tests

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

잘못된 토큰은 저장하지 않는다.
