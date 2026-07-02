# jobs

Background work orchestration.

Owns job interfaces, sync runner, queued backend adapters, retry metadata, and
dead-letter handling.

`CachePurgeJobPayload` (`cache_purge_payload.py`) is a `JobPayload` subclass
for a background cache purge job: it exposes `job_type` as
`CACHE_PURGE_JOB_TYPE` (`"cache.purge"`). It carries `source` and
`parser_version` for a scoped purge (mirroring the arguments
`invalidate_render_cache` in `modules/cache/invalidate.py` takes), or a
`purge_all` flag to request a full cache clear (mirroring
`Cache.clear_all()`) instead — when `purge_all=True`, any given `source` is
ignored. Since `purge_all` defaults to `False`, `source` is required (and
cannot be empty/whitespace-only) unless `purge_all=True`, raising
`InvalidCachePurgeJobPayloadError` otherwise.

`CachePurgeJobHandler` (`cache_purge_handler.py`) is the `JobHandler` that
executes a `CachePurgeJobPayload`. It is constructed with a `CacheBackend`
and, on `handle()`, calls `Cache.clear_all()` when `purge_all=True` or
`invalidate_render_cache` otherwise. Since `JobHandler.handle()` is a
synchronous contract but the cache module is async, the handler wraps the
call in `asyncio.run`. It returns `JobResult.fail(...)` if given a payload
that isn't a `CachePurgeJobPayload`.

`SearchIndexJobHandler` (`search_index_handler.py`) is the `JobHandler` that
executes an `IndexDocumentJobPayload` from `modules/search`, exposing
`job_type` as `SEARCH_INDEX_JOB_TYPE` (`"search.index"`). It is constructed
with a `SearchAdapter` and, on `handle()`, converts the payload to a
`SearchDocument` (via `to_search_document()`) and calls the adapter's async
`index()`, wrapped in `asyncio.run` for the same synchronous-contract reason
as `CachePurgeJobHandler`. It returns `JobResult.fail(...)` if given a
payload that isn't an `IndexDocumentJobPayload`.

`BacklinkRefreshJobPayload` (`backlink_refresh_payload.py`) is a `JobPayload`
subclass for a background backlink index refresh job: it exposes `job_type`
as `BACKLINK_REFRESH_JOB_TYPE` (`"backlink.refresh"`). It carries
`page_name`, the document whose links changed and whose targets' backlink
entries need recomputing. `page_name` is required and cannot be
empty/whitespace-only, raising `InvalidBacklinkRefreshJobPayloadError`
otherwise.

`BacklinkRefreshJobHandler` (`backlink_refresh_handler.py`) is a placeholder
`JobHandler` for `BacklinkRefreshJobPayload`, exposing `job_type` as
`BACKLINK_REFRESH_JOB_TYPE`. There is no backlinks module yet to actually
recompute backlink index entries, so `handle()` only validates the payload
type and returns `JobResult.ok(data={"page_name": payload.page_name})`. It
returns `JobResult.fail(...)` if given a payload that isn't a
`BacklinkRefreshJobPayload`. The real backlink index update logic replaces
this placeholder in a later task once a backlinks module exists.

`CategoryRefreshJobPayload` (`category_refresh_payload.py`) is a `JobPayload`
subclass for a background category index refresh job: it exposes `job_type`
as `CATEGORY_REFRESH_JOB_TYPE` (`"category.refresh"`). It carries
`category_name`, the category whose membership changed and whose index needs
recomputing. `category_name` is required and cannot be empty/whitespace-only,
raising `InvalidCategoryRefreshJobPayloadError` otherwise.

`CategoryRefreshJobHandler` (`category_refresh_handler.py`) is a placeholder
`JobHandler` for `CategoryRefreshJobPayload`, exposing `job_type` as
`CATEGORY_REFRESH_JOB_TYPE`. There is no categories module yet to actually
recompute category index entries, so `handle()` only validates the payload
type and returns `JobResult.ok(data={"category_name": payload.category_name})`.
It returns `JobResult.fail(...)` if given a payload that isn't a
`CategoryRefreshJobPayload`. The real category index update logic replaces
this placeholder in a later task once a categories module exists.

`RecentChangesJobPayload` (`recent_changes_payload.py`) is a `JobPayload`
subclass for a background job that records an edit into the recent changes
list: it exposes `job_type` as `RECENT_CHANGES_JOB_TYPE`
(`"recent_changes.record"`). It carries `page_name` (the document that was
edited), `author_id` (who made the edit), `occurred_at` (when the edit
happened), and an optional `summary` (defaulting to `""`). `page_name` is
required and cannot be empty/whitespace-only, and `occurred_at` is required,
raising `InvalidRecentChangesJobPayloadError` otherwise. The handler that
actually records the entry is added in a later task; this payload only
defines the data contract.

`RecentChangesJobHandler` (`recent_changes_handler.py`) is a placeholder
`JobHandler` for `RecentChangesJobPayload`, exposing `job_type` as
`RECENT_CHANGES_JOB_TYPE`. There is no recent changes module yet to actually
record the entry, so `handle()` only validates the payload type and returns
`JobResult.ok(data={...})` with `page_name`, `author_id`, `occurred_at`, and
`summary`. It returns `JobResult.fail(...)` if given a payload that isn't a
`RecentChangesJobPayload`. The real recent changes recording logic replaces
this placeholder in a later task once a recent changes module exists.

`JobAuditEvent` (`audit_event.py`) is a domain model recording the outcome
of a job run: it carries `id`, `action` (a `JobAuditAction` of
`JOB_SUCCEEDED` or `JOB_FAILED`), `job_type` (mirroring `JobPayload.job_type`
/ `DeadLetter.job_type`), `occurred_at`, and an optional `error`. `id` and
`job_type` are required and cannot be empty/whitespace-only, raising
`EmptyJobAuditEventIdError` / `MissingJobTypeError` otherwise. `error` is
required when `action` is `JOB_FAILED` and forbidden when `action` is
`JOB_SUCCEEDED`, raising `InvalidJobAuditEventError` otherwise (mirroring the
success/error contract of `JobResult`). `is_succeeded()` / `is_failed()`
report which outcome the event records. Persisting events is left to a later
task, once a storage-backed implementation exists.

`JobAuditRecorder` (`audit_recorder.py`) is the service that creates and
accumulates `JobAuditEvent`s in memory. It currently only records job
failures: `record_job_failed(job_type, error)` builds a `JobAuditEvent` with
a generated `id`, `action=JOB_FAILED`, and `occurred_at` set to the current
UTC time, appends it, and returns it. `events()` returns a copy of the
recorded events in order. `SyncJobRunner` (`runner.py`) is constructed with
an optional `audit_recorder` (defaulting to a new `JobAuditRecorder()`) and
calls `record_job_failed(job_type=payload.job_type, error=result.error)`
whenever `run()` produces a `FAILED` outcome, whether the handler returned a
failed `JobResult` or raised an exception. Recording on success is added in
a later task.
