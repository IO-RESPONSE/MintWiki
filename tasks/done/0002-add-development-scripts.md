# 0002 Add Development Scripts

## Goal

Add lightweight scripts for bootstrap, test, QA, and runner entrypoints.

## Scope

- `scripts/bootstrap.sh`
- `scripts/test.sh`
- `scripts/qa.sh`
- `scripts/run-next-task.sh`

## Acceptance Criteria

- Scripts are executable.
- `scripts/test.sh` can run even before database-backed modules exist.
- `scripts/qa.sh` performs at least syntax/import checks or delegates to tests.
- `scripts/run-next-task.sh` documents the expected runner contract.

## Out of Scope

- Full Codex automation.
- systemd installation.
- Git server setup.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`
