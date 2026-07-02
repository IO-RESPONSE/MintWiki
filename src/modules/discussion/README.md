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

## Comment Moderation Rules

### 1. Moderation is a single action: hiding a comment

The only moderation primitive is `DiscussionComment.hide()` (`comment.py`),
called through `DiscussionService.hide_comment()` (`service.py`). It sets
`is_hidden = True` and stamps `hidden_at`. There is no `unhide()`/`show()`
counterpart anywhere in the module — once a comment is hidden there is no
way to reverse it through this module's API. Hiding is also unconditional:
it can be called on an already-hidden comment (idempotent re-hide, only
`hidden_at` advances) exactly like `close()`/`pause()` on threads.

### 2. Hiding does not delete content — it changes which view exposes it

`DiscussionComment` renders two views (`to_public_view()`/
`to_moderator_view()`, `comment.py`). Both include the same non-body fields
(`id`, `thread_id`, `created_by`, `created_at`, `is_hidden`, `hidden_at`);
only `body` differs. The public view masks `body` to `None` when
`is_hidden` is `True`; the moderator view always returns the real `body`
regardless of `is_hidden`. The underlying `DiscussionComment.body` itself is
never cleared or overwritten by `hide()` — moderation is purely a rendering
decision made by whichever view function the caller chooses to call. See
`test_comment.py::TestDiscussionCommentPublicView` and
`::TestDiscussionCommentModeratorView`.

### 3. Nothing gates who may choose the moderator view

`hide_comment(comment_id, actor_id=None)` accepts an arbitrary, optional
`actor_id` string with no validation against ACL roles, no check that the
caller has any particular `Permission`, and no relationship enforced
between `actor_id` and the comment's `created_by`. Likewise, choosing
`to_moderator_view()` over `to_public_view()` is a plain method call with no
guard — any caller with a `DiscussionComment` reference can request the
moderator rendering. There is no `Permission.MODERATE` (or similar) entry in
`modules/acl/permission.py`; `require_discuss_permission()` in `router.py`
only gates *participation* (`Permission.DISCUSS`) and is not wired to
`hide_comment` in any way. See
`test_service.py::TestDiscussionServiceHideComment::test_hide_comment_records_audit_event`,
where `actor_id="moderator1"` is accepted as a bare string with no
role lookup.

### 4. `hide_comment` is not reachable over HTTP yet

`router.py` exposes `POST /threads/{id}/comments` and
`GET /threads/{id}/comments`, but no route calls
`DiscussionService.hide_comment()`. Moderation is reachable only
in-process (service/repository) and in tests today, mirroring the same gap
already noted for `reopen_thread()`/`pause_thread()` in the state machine
section above.

### 5. Every hide is audited, with the actor recorded as given

`DiscussionService.hide_comment()` always calls
`DiscussionAuditRecorder.record_comment_hidden()` after a successful hide,
producing a `DiscussionAuditEvent` with `action=COMMENT_HIDDEN`,
`comment_id`, `thread_id`, and `actor_id` copied verbatim from the caller
(no default fallback the way `record_thread_created()` falls back to
`thread.created_by` when `actor_id` is omitted — an omitted `actor_id` on a
hide is recorded as `None`). Hiding a nonexistent comment raises
`DiscussionCommentNotFoundError` before any audit event is recorded — no
"hide failed" event exists. See
`test_service.py::TestDiscussionServiceHideComment::test_hide_comment_records_audit_event`
and `::test_hide_nonexistent_comment_does_not_record_audit_event`.

## Testing (Moderation)

Moderation behavior is tested in:

- `tests/modules/discussion/test_comment.py::TestDiscussionCommentHide`,
  `::TestDiscussionCommentPublicView`, `::TestDiscussionCommentModeratorView`
  — `hide()` and the public/moderator view split
- `tests/modules/discussion/test_service.py::TestDiscussionServiceHideComment`
  — service-level hide delegation, not-found handling, and audit recording
- `tests/modules/discussion/test_service.py::TestDiscussionServiceModeratorViewsHiddenComment`
  — end-to-end: hide via the service, then read both views back
- `tests/modules/discussion/test_audit_recorder.py::TestDiscussionAuditRecorderRecordCommentHidden`
  — `record_comment_hidden()` in isolation, including the `actor_id=None`
  case
