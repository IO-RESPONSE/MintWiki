# 0003 Add systemd Runner Units

## Goal

Add example systemd service and timer files for a 10-minute task runner.

## Scope

- `ops/systemd/wiki-engine-runner.service`
- `ops/systemd/wiki-engine-runner.timer`
- `docs/runner.md`

## Acceptance Criteria

- Timer is configured for 10-minute intervals.
- Service calls `scripts/run-next-task.sh`.
- Documentation explains lock handling and non-overlap behavior.

## Out of Scope

- Installing units into `/etc/systemd/system`.
- Creating Linux users.
- Starting services.

## QA

- Manual file review.
