#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: scripts/codex-runner.sh TASK_FILE RUN_DIR" >&2
  exit 64
fi

TASK_FILE="$1"
RUN_DIR="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_SANDBOX="${CODEX_SANDBOX:-workspace-write}"
CODEX_APPROVAL="${CODEX_APPROVAL:-never}"

cd "$ROOT_DIR"
mkdir -p "$RUN_DIR"

PROMPT_FILE="$RUN_DIR/prompt.md"
FINAL_FILE="$RUN_DIR/final.md"
EVENTS_FILE="$RUN_DIR/events.jsonl"

cat > "$PROMPT_FILE" <<PROMPT
You are running as a non-interactive implementation worker for this repository.

Read and complete exactly this task:

$(cat "$TASK_FILE")

Repository rules:
- Keep the change narrowly scoped to the task.
- Prefer existing project patterns.
- Add or update tests required by the task.
- Run scripts/test.sh before finishing if possible.
- Do not implement work listed as Out of Scope.
- Do not wait for user input.
- Leave a concise final summary.
PROMPT

ARGS=(
  exec
  --cd "$ROOT_DIR"
  --sandbox "$CODEX_SANDBOX"
  --ask-for-approval "$CODEX_APPROVAL"
  --json
  --output-last-message "$FINAL_FILE"
)

if [ -n "${CODEX_MODEL:-}" ]; then
  ARGS+=(--model "$CODEX_MODEL")
fi

"$CODEX_BIN" "${ARGS[@]}" - < "$PROMPT_FILE" > "$EVENTS_FILE"

