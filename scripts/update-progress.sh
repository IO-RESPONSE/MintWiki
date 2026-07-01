#!/usr/bin/env bash
# README.md 의 <!-- PROGRESS:START --> ~ <!-- PROGRESS:END --> 블록을
# 현재 태스크 큐 진행 현황으로 갱신한다. 러너가 매 사이클 커밋 직전에 호출한다.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="$(date '+%Y-%m-%d %H:%M %Z')"

TS="$TS" python3 - <<'PY'
import os, re, glob, sys

def count(d):
    return len(glob.glob(f"tasks/{d}/*.md"))

def ids(d):
    out = []
    for f in glob.glob(f"tasks/{d}/*.md"):
        b = os.path.basename(f)[:4]
        if b.isdigit():
            out.append(int(b))
    return sorted(out)

def name(d, i):
    g = glob.glob(f"tasks/{d}/{i:04d}-*.md")
    return os.path.basename(g[0])[:-3] if g else "-"

done   = count("done")
queue  = count("queue")
failed = count("failed")
inprog = count("in-progress")
total  = done + queue + failed + inprog
pct    = (done / total * 100) if total else 0.0

done_ids  = ids("done")
queue_ids = ids("queue")
last = name("done", done_ids[-1]) if done_ids else "-"
nxt  = name("queue", queue_ids[0]) if queue_ids else "-"

ts = os.environ.get("TS", "")
filled = round(pct / 2)          # 50칸 막대
bar = "█" * filled + "░" * (50 - filled)

fail_line = f"| ❌ 실패 | {failed} |\n" if failed else ""

block = f"""<!-- PROGRESS:START -->
**진행률: {done} / {total} ({pct:.1f}%)**

`{bar}`

| 구분 | 개수 |
|---|---|
| ✅ 완료 | {done} |
| ⏳ 대기 | {queue} |
{fail_line}
- 최근 완료: `{last}`
- 갱신: {ts}
<!-- PROGRESS:END -->"""

path = "README.md"
with open(path, encoding="utf-8") as fh:
    s = fh.read()

new = re.sub(r"<!-- PROGRESS:START -->.*?<!-- PROGRESS:END -->", block, s, flags=re.S)
if new == s and "PROGRESS:START" not in s:
    sys.stderr.write("README 에 PROGRESS 마커가 없어 갱신하지 못했습니다.\n")
    sys.exit(0)
with open(path, "w", encoding="utf-8") as fh:
    fh.write(new)
print(f"README 진행 현황 갱신: {done}/{total} ({pct:.1f}%)")
PY
