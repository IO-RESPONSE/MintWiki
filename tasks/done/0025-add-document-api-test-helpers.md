# 0025 Add Document API Test Helpers

## Goal

Add reusable test helpers for document API tests.

## Scope

- `tests/conftest.py`
- `tests/modules/document/`

## Acceptance Criteria

- Tests can create an app instance through a fixture.
- Document API tests use the fixture.
- Existing tests pass.

## Out of Scope

- Changing production dependency injection.
- Database test fixtures.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

