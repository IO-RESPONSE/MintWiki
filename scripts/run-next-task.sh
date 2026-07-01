#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${WIKI_ENGINE_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOCK_FILE="${WIKI_ENGINE_LOCK:-/tmp/wiki-engine-runner.lock}"
RUNS_DIR="${WIKI_ENGINE_RUNS_DIR:-$ROOT_DIR/runs}"
QUEUE_DIR="$ROOT_DIR/tasks/queue"
IN_PROGRESS_DIR="$ROOT_DIR/tasks/in-progress"
DONE_DIR="$ROOT_DIR/tasks/done"
FAILED_DIR="$ROOT_DIR/tasks/failed"
AGENT="${WIKI_ENGINE_AGENT:-claude}"

if [ -n "${GITHUB_TOKEN_FILE:-}" ]; then
  export GIT_ASKPASS="${GIT_ASKPASS:-$ROOT_DIR/scripts/github-token-askpass.sh}"
  export GIT_TERMINAL_PROMPT="${GIT_TERMINAL_PROMPT:-0}"
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another runner is already active."
  exit 0
fi

cd "$ROOT_DIR"
mkdir -p "$QUEUE_DIR" "$IN_PROGRESS_DIR" "$DONE_DIR" "$FAILED_DIR" "$RUNS_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree has uncommitted changes. Refusing to start a new task." >&2
  exit 2
fi

if git remote get-url origin >/dev/null 2>&1; then
  git pull --ff-only
fi

TASK_PATH="$(find "$QUEUE_DIR" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
if [ -z "$TASK_PATH" ]; then
  echo "No queued task."
  exit 0
fi

TASK_NAME="$(basename "$TASK_PATH")"
ACTIVE_TASK="$IN_PROGRESS_DIR/$TASK_NAME"
RUN_ID="$(date '+%Y%m%d-%H%M%S')-${TASK_NAME%.md}"
RUN_DIR="$RUNS_DIR/$RUN_ID"
mkdir -p "$RUN_DIR"

mv "$TASK_PATH" "$ACTIVE_TASK"
echo "$TASK_NAME" > "$RUN_DIR/task-name.txt"
cp "$ACTIVE_TASK" "$RUN_DIR/task.md"

finish_failed() {
  local exit_code="$1"
  {
    echo "Task failed with exit code $exit_code"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z %z')"
  } > "$RUN_DIR/failure.txt"
  if [ -f "$ACTIVE_TASK" ]; then
    mv "$ACTIVE_TASK" "$FAILED_DIR/$TASK_NAME"
  fi
  echo "Task failed: $TASK_NAME" >&2
  exit "$exit_code"
}

trap 'finish_failed $?' ERR

case "$AGENT" in
  claude)
    scripts/claude-runner.sh "$ACTIVE_TASK" "$RUN_DIR"
    ;;
  codex)
    scripts/codex-runner.sh "$ACTIVE_TASK" "$RUN_DIR"
    ;;
  *)
    echo "Unsupported WIKI_ENGINE_AGENT: $AGENT" >&2
    exit 64
    ;;
esac
scripts/test.sh
scripts/qa.sh

mv "$ACTIVE_TASK" "$DONE_DIR/$TASK_NAME"

git add .
git commit -m "태스크 ${TASK_NAME%.md} 완료"

if git remote get-url origin >/dev/null 2>&1; then
  git push
fi

echo "Task complete: $TASK_NAME"
