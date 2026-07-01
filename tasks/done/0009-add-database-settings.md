# 0009 Add Database Settings

## Goal

Add database and cache URL settings to the app config object.

## Scope

- `src/app/config.py`
- `tests/test_config.py`

## Acceptance Criteria

- Settings expose `database_url`.
- Settings expose `redis_url`.
- Defaults are safe for local development.
- Tests verify defaults.

## Out of Scope

- Opening database connections.
- Docker Compose changes.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

