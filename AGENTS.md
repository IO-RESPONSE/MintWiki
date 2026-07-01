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
