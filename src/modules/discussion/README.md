# discussion

Document discussion workflows.

Owns threads, comments, thread state, discussion-specific logs, and discussion
ACL integration.

## Discussion Thread State Machine

### 1. Three states exist, but transitions are not gated by current state

`DiscussionThread.status` (`thread.py`) is a plain string with three values:
`"open"` (default), `"closed"`, `"paused"`. `ThreadState` (`state.py`) is a
separate `Enum` with matching string values (`OPEN`/`CLOSED`/`PAUSED`), but
nothing in `thread.py`, `service.py`, `repository.py`, `schema.py`, or
`router.py` references `ThreadState` — `status` is never validated against
it, and the enum is not wired into the model. See `test_state.py` for the
enum in isolation.

Every transition method (`close()`, `reopen()`, `pause()`) is unconditional:
it can be called from any current status, including its own status
(idempotent), or from either of the other two — there is no "illegal
transition". `pause()` on an already-closed thread succeeds and overwrites
`status` to `"paused"` (see
`test_thread.py::TestDiscussionThreadState::test_pause_from_closed_marks_thread_paused`),
and `close()` on a paused thread succeeds the same way
(`test_close_from_paused_marks_thread_closed`). Repeated calls to
`close()`/`pause()` keep `status` unchanged but keep advancing the
corresponding timestamp
(`test_close_is_idempotent_and_updates_closed_at`,
`test_pause_is_idempotent_and_updates_paused_at`).

### 2. `closed_at`/`paused_at` are not mutually exclusive or cleared on transition

Only `reopen()` clears a timestamp (`closed_at = None`); it does not touch
`paused_at`. `close()` sets `closed_at` but never resets `paused_at`, and
`pause()` sets `paused_at` but never resets `closed_at`. A thread that went
`open -> paused -> closed` still carries a non-`None` `paused_at` while
`status == "closed"`, and a thread that went `paused -> reopen` keeps its
stale `paused_at` even though `status == "open"`. Callers must key off
`status` alone, not off "is `closed_at`/`paused_at` set", to determine the
current state. See
`test_thread.py::TestDiscussionThreadState::test_full_state_cycle_through_all_transitions`.

### 3. `is_open()`/`is_paused()` are derived, not stored

Both are plain string comparisons against `status` (`status == "open"`,
`status == "paused"`); there is no `is_closed()` helper — checking for closed
means `not is_open() and not is_paused()`.

### 4. State does not gate comments — it is informational only

Nothing in `DiscussionService.add_comment()` or `hide_comment()` checks
`thread.is_open()`/`is_paused()` before writing. A comment can be added to
(or hidden on) a closed or paused thread exactly as on an open one;
"no new comments while closed" is not enforced anywhere. `router.py` only
exposes `POST /threads/{id}/close` — `reopen_thread()` and `pause_thread()`
exist on `DiscussionService` but have no route wired to them yet, so they are
reachable in-process and in tests only, not over HTTP.

### 5. Audit coverage of transitions is partial

`DiscussionAuditAction` (`audit_event.py`) defines `THREAD_CLOSED`,
`THREAD_REOPENED`, and `THREAD_PAUSED` members, but `DiscussionAuditRecorder`
(`audit_recorder.py`) only implements `record_thread_created()` and
`record_comment_hidden()` — there is no
`record_thread_closed`/`record_thread_reopened`/`record_thread_paused`
method, and `DiscussionService.close_thread()`/`reopen_thread()`/
`pause_thread()` never call the audit recorder. Calling `.close()`/
`.reopen()`/`.pause()` via the service changes `status` with no audit trail;
only thread creation and comment hiding produce `DiscussionAuditEvent`s
today.

## Testing

State transition behavior is tested in:

- `tests/modules/discussion/test_state.py` — `ThreadState` enum values
- `tests/modules/discussion/test_thread.py::TestDiscussionThreadState` —
  transition methods, idempotency, and cross-state transitions
  (closed→paused, paused→closed, paused→open, full cycle)
- `tests/modules/discussion/test_service.py` — service-level close/reopen/
  pause delegation to the repository and not-found handling
- `tests/modules/discussion/test_audit_event.py` and `test_audit_recorder.py`
  — audit action enum and the (partial) recorder coverage described above
