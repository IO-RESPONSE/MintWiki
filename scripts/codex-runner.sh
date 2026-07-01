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
- Do NOT create, move, rename, or delete any file under the tasks/ directory. The runner manages the task queue; touching tasks/ will break the runner.
- Do not wait for user input.
- Write all code comments and docstrings in Korean. Keep identifiers (variable, function, class names) in English.
- Leave a concise final summary.
PROMPT

GLOBAL_ARGS=()
if [ -n "$CODEX_APPROVAL" ]; then
  GLOBAL_ARGS+=(--ask-for-approval "$CODEX_APPROVAL")
fi

ARGS=(
  exec
  --cd "$ROOT_DIR"
  --sandbox "$CODEX_SANDBOX"
  --json
  --output-last-message "$FINAL_FILE"
)

if [ -n "${CODEX_MODEL:-}" ]; then
  ARGS+=(--model "$CODEX_MODEL")
fi

"$CODEX_BIN" "${GLOBAL_ARGS[@]}" "${ARGS[@]}" - < "$PROMPT_FILE" > "$EVENTS_FILE"
