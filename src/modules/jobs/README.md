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
`InvalidCachePurgeJobPayloadError` otherwise. The job handler that actually
calls into the `cache` module to perform the purge is added by a later task;
this payload only defines the data contract.
