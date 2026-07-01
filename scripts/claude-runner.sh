#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: scripts/claude-runner.sh TASK_FILE RUN_DIR" >&2
  exit 64
fi

TASK_FILE="$1"
RUN_DIR="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
CLAUDE_PERMISSION_MODE="${CLAUDE_PERMISSION_MODE:-acceptEdits}"
CLAUDE_OUTPUT_FORMAT="${CLAUDE_OUTPUT_FORMAT:-json}"
CLAUDE_MAX_BUDGET_USD="${CLAUDE_MAX_BUDGET_USD:-}"

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
  --print
  --permission-mode "$CLAUDE_PERMISSION_MODE"
  --output-format "$CLAUDE_OUTPUT_FORMAT"
)

if [ -n "${CLAUDE_MODEL:-}" ]; then
  ARGS+=(--model "$CLAUDE_MODEL")
fi

if [ -n "$CLAUDE_MAX_BUDGET_USD" ]; then
  ARGS+=(--max-budget-usd "$CLAUDE_MAX_BUDGET_USD")
fi

"$CLAUDE_BIN" "${ARGS[@]}" < "$PROMPT_FILE" > "$EVENTS_FILE"

if [ "$CLAUDE_OUTPUT_FORMAT" = "json" ]; then
  cp "$EVENTS_FILE" "$FINAL_FILE"
else
  tail -n 200 "$EVENTS_FILE" > "$FINAL_FILE"
fi
