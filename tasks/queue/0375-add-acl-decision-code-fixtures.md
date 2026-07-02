# 0375 Add ACL decision code fixtures

## Goal

ACL decision 결과 코드를 fixture로 고정한다.

## Phase

Phase A: PHP Replacement Contract, 0351-0390.

## Scope

- src/modules/acl
- tests

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

allow/deny/reason code를 언어 독립화한다.
