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
