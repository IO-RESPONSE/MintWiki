# Codex Repository Rules

This repository is organized around small, explicit tasks that should fit in a
short runner cycle. Treat each task file as the source of truth for goal, scope,
acceptance criteria, out-of-scope items, and QA.

## 10-Minute Task Workflow

1. Read the assigned task completely before changing files.
2. Inspect the relevant existing files and follow current project patterns.
3. Make the narrowest change that satisfies the task acceptance criteria.
4. Add or update tests only when the task requires behavior that should be
   verified by tests.
5. Run the task's QA commands before finishing when possible.
6. Leave a concise final summary with what changed and which checks ran.

Complete exactly one task per runner cycle. Do not start the next queued task,
even if the current task is small or finishes quickly.

**`tasks/` 디렉토리는 절대 건드리지 않는다.** 태스크 파일을 생성·이동·이름변경·
삭제하지 않는다. 태스크 큐(queue/in-progress/done/failed 이동)는 러너가 전담한다.
에이전트가 `tasks/`를 손대면 러너가 깨진다.

## 언어 규칙 (Language)

- 코드 주석과 docstring은 **한글**로 작성한다.
- 커밋 메시지와 문서(README 등)는 **한글**로 작성한다.
- 단, 식별자(변수·함수·클래스·모듈명)와 코드 자체는 **영문**을 유지한다.

## Scope Discipline

Do not implement work listed in a task's Out of Scope section. If an
out-of-scope item seems necessary, stop at the in-scope change and report the
constraint instead of expanding the task.

## Test and QA Commands

Use these repository-level checks:

```bash
scripts/test.sh
scripts/qa.sh
```

Run `scripts/test.sh` before finishing whenever possible. Run `scripts/qa.sh`
when the task requests full QA or before final handoff for changes that should
pass the repository quality gate.
