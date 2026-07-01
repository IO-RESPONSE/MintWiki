# 0005 Add Env Example

## Goal

Add a documented environment variable example file.

## Scope

- `.env.example`
- `README.md`

## Acceptance Criteria

- `.env.example` includes app name and environment values.
- `.env.example` includes placeholder database and Redis URLs.
- README mentions copying `.env.example` to `.env` for local runs.

## Out of Scope

- Creating real secrets.
- Connecting to the database.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

