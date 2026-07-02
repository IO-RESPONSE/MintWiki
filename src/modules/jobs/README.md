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
otherwise. The handler that performs the actual backlink index update is
added in a later task; this payload only defines the data contract.
