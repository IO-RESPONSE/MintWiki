# 10-Minute Job Model

## Purpose

Every task must be small enough for an automated runner to implement, test, and
commit in a short cycle. More tasks are acceptable. Ambiguous tasks are not.

## Job Rules

- One job changes one small behavior.
- Prefer 1 to 5 touched files.
- Add or update tests in the same job.
- Include explicit acceptance criteria.
- Avoid broad refactors.
- Avoid multiple modules unless the task is an integration task.
- Make failures easy to retry.
- Do not leave generated or local-only files untracked unless documented.

## Job Lifecycle

```text
tasks/queue
  -> tasks/in-progress
  -> tasks/done
  -> tasks/failed
```

## Runner Contract

For each queued task, the runner should:

1. Pull the latest repository state.
2. Move one task into `tasks/in-progress`.
3. Execute the implementation agent with the task file as input.
4. Run `scripts/test.sh`.
5. Run `scripts/qa.sh`.
6. Move the task to `tasks/done` on success.
7. Move the task to `tasks/failed` on failure and record a failure note.
8. Commit and push only when tests and QA pass.

## Good Job Examples

- Add app config object with environment defaults.
- Add health endpoint.
- Add title normalization function.
- Add document table migration.
- Add repository test for document lookup miss.
- Add parser fixture for bold inline syntax.

## Bad Job Examples

- Implement ACL.
- Build search.
- Finish parser.
- Add admin dashboard.
- Make production deployment.

These must be split into interface, storage, service, route, fixture, and
integration jobs.
