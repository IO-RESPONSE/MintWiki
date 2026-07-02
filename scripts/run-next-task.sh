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

if [ "${WIKI_ENGINE_GIT_SYNC:-1}" != "0" ] && git remote get-url origin >/dev/null 2>&1; then
  git pull --ff-only
fi

TASK_PATH="$(
  find "$QUEUE_DIR" -maxdepth 1 -type f -name '*.md' | sort | while IFS= read -r candidate; do
    task_file="$(basename "$candidate")"
    task_number="${task_file%%-*}"
    case "$task_number" in
      ''|*[!0-9]*) continue ;;
    esac
    if [ -n "${WIKI_ENGINE_TASK_MIN:-}" ] && [ "$task_number" -lt "$WIKI_ENGINE_TASK_MIN" ]; then
      continue
    fi
    if [ -n "${WIKI_ENGINE_TASK_MAX:-}" ] && [ "$task_number" -gt "$WIKI_ENGINE_TASK_MAX" ]; then
      continue
    fi
    printf '%s\n' "$candidate"
    break
  done
)"
if [ -z "$TASK_PATH" ]; then
  echo "No queued task."
  exit 0
fi

TASK_NAME="$(basename "$TASK_PATH")"
ACTIVE_TASK="$IN_PROGRESS_DIR/$TASK_NAME"
RUN_ID="$(date '+%Y%m%d-%H%M%S')-${TASK_NAME%.md}"
RUN_DIR="$RUNS_DIR/$RUN_ID"
BASE_COMMIT="$(git rev-parse HEAD)"
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
  local failed_task_tmp="$RUN_DIR/$TASK_NAME"
  if [ -f "$ACTIVE_TASK" ]; then
    cp "$ACTIVE_TASK" "$failed_task_tmp" || true
  elif [ -f "$QUEUE_DIR/$TASK_NAME" ]; then
    cp "$QUEUE_DIR/$TASK_NAME" "$failed_task_tmp" || true
  fi
  # 실패 시 워킹트리를 마지막 커밋 상태로 되돌려, 다음 사이클이 dirty tree 로 막히지 않게 한다.
  # (runs/ 는 gitignore 라 clean 에서 제외되어 실패 로그는 보존된다.)
  git reset --hard HEAD >/dev/null 2>&1 || true
  git clean -fd >/dev/null 2>&1 || true
  # 실패한 태스크를 failed/ 로 이동하고 커밋해 트리를 clean 상태로 만든다.
  mkdir -p "$FAILED_DIR"
  if [ -f "$failed_task_tmp" ]; then
    # git reset --hard 가 큐 파일(queue/TASK)을 되살리므로, 명시적으로 큐에서 제거해
    # 실패 태스크가 failed/ 에만 남게 한다. 이렇게 하지 않으면 다음 사이클이 같은
    # 태스크를 다시 집어 무한 실패 루프에 빠진다.
    rm -f "$QUEUE_DIR/$TASK_NAME"
    mv "$failed_task_tmp" "$FAILED_DIR/$TASK_NAME"
    git add -A >/dev/null 2>&1 || true
    git commit -q -m "태스크 ${TASK_NAME%.md} 실패" >/dev/null 2>&1 || true
  fi
  echo "Task failed: $TASK_NAME" >&2
  exit "$exit_code"
}

trap 'finish_failed $?' ERR

# 에이전트(claude/codex) 호출 단계.
# 이 단계의 실패는 대개 rate-limit·네트워크 등 인프라 사유다. 그런 실패까지
# "태스크 실패"로 처리하면(→ failed/ 이동) 멀쩡한 태스크가 스킵되어 구멍이 난다.
# 따라서 에이전트 실패 시에는 워킹트리를 되돌려 태스크를 큐에 남기고 조용히
# 종료해, 다음 사이클(또는 5h 윈도우 리셋 후)에 재시도되게 한다.
# (test/qa 실패만 진짜 실패로 보고 finish_failed 로 failed/ 처리한다.)
trap - ERR
set +e
case "$AGENT" in
  claude)
    scripts/claude-runner.sh "$ACTIVE_TASK" "$RUN_DIR"
    ;;
  codex)
    scripts/codex-runner.sh "$ACTIVE_TASK" "$RUN_DIR"
    ;;
  *)
    echo "Unsupported WIKI_ENGINE_AGENT: $AGENT" >&2
    set -e
    exit 64
    ;;
esac
agent_rc=$?
set -e
if [ "$agent_rc" -ne 0 ]; then
  echo "Agent 호출 실패(rc=$agent_rc) — rate-limit/인프라 추정. 태스크를 큐에 남기고 종료." >&2
  git reset --hard HEAD >/dev/null 2>&1 || true
  git clean -fd >/dev/null 2>&1 || true
  exit 0
fi
trap 'finish_failed $?' ERR
scripts/test.sh
scripts/qa.sh

mv "$ACTIVE_TASK" "$DONE_DIR/$TASK_NAME"

if [ "${WIKI_ENGINE_SKIP_PROGRESS:-0}" != "1" ]; then
  scripts/update-progress.sh || true
fi

if [ "$(git rev-parse HEAD)" != "$BASE_COMMIT" ]; then
  git reset --soft "$BASE_COMMIT"
fi

git add -A
git commit -m "태스크 ${TASK_NAME%.md} 완료"

if [ "${WIKI_ENGINE_GIT_SYNC:-1}" != "0" ] && git remote get-url origin >/dev/null 2>&1; then
  git push
fi

echo "Task complete: $TASK_NAME"
