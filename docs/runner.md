# Non-Interactive Runner

The automated loop is:

```text
systemd timer
  -> scripts/run-next-task.sh
  -> scripts/claude-runner.sh or scripts/codex-runner.sh
  -> claude --print or codex exec
  -> scripts/test.sh
  -> scripts/qa.sh
  -> git commit
  -> git push, when origin exists
```

## Requirements

- The repository must be a Git repository.
- `claude` or `codex` must be installed and authenticated for non-interactive use.
- The runner process must have write access to the repository.
- The working tree must be clean before a task starts.

This server currently has `codex exec`, which is the documented non-interactive
Codex mode for scripts and scheduled jobs.

## Environment

The runner reads these optional environment variables:

```text
WIKI_ENGINE_REPO=/root/wiki-engine-blueprint
WIKI_ENGINE_LOCK=/tmp/wiki-engine-runner.lock
WIKI_ENGINE_RUNS_DIR=/root/wiki-engine-blueprint/runs
WIKI_ENGINE_AGENT=claude
CLAUDE_BIN=claude
CLAUDE_PERMISSION_MODE=acceptEdits
CLAUDE_OUTPUT_FORMAT=json
CLAUDE_MODEL=
CLAUDE_MAX_BUDGET_USD=
CODEX_BIN=codex
CODEX_MODEL=
CODEX_SANDBOX=workspace-write
CODEX_APPROVAL=never
```

`WIKI_ENGINE_AGENT=claude` makes the timer use Claude Code by default.
Set `WIKI_ENGINE_AGENT=codex` to switch back to Codex.

`CLAUDE_PERMISSION_MODE=acceptEdits` is the default because Claude Code refuses
`bypassPermissions` when run as root. If you later run the systemd service as a
non-root dedicated user in an isolated runner, you can evaluate
`bypassPermissions`.

Set `CLAUDE_MAX_BUDGET_USD` to cap spend for each print-mode invocation.

`CODEX_APPROVAL=never` is important for unattended Codex execution. If Codex
needs an action that requires approval, that run should fail instead of hanging.

## Safety Behavior

- The runner uses `flock` to prevent overlapping runs.
- The runner refuses to start when the working tree is dirty.
- On success, the task moves from `tasks/queue` to `tasks/done`.
- On failure, the task moves to `tasks/failed` and run logs remain under `runs/`.
- Failed code changes are left in the working tree for inspection.

Because failed code changes are not automatically reverted, the next task will
not start until a human reviews or cleans the working tree.

## Manual Run

```bash
cd /root/wiki-engine-blueprint
scripts/run-next-task.sh
```

## systemd

Example unit files live under `ops/systemd/`.

Install manually after review:

```bash
sudo cp ops/systemd/wiki-engine-runner.service /etc/systemd/system/
sudo cp ops/systemd/wiki-engine-runner.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wiki-engine-runner.timer
```

Check status and logs:

```bash
systemctl status wiki-engine-runner.timer
journalctl -u wiki-engine-runner.service -f
```
