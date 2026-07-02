# jobs

Background work orchestration.

Owns job interfaces, sync runner, queued backend adapters, retry metadata, and
dead-letter handling.

## Execution Models: Sync vs Queued Runner

The jobs module supports two execution models for running background jobs:

### SyncJobRunner: Synchronous Execution

`SyncJobRunner` (`runner.py`) executes jobs immediately in the calling thread
with a synchronous contract. It takes a `JobHandler` and `JobPayload`, invokes
`handler.handle(payload)` directly, and returns the result immediately. If the
handler raises an exception, `SyncJobRunner` catches it and converts it to a
failed `JobResult`, ensuring the caller always gets a `JobRunOutcome` with a
status (SUCCEEDED or FAILED) and a result.

**Use SyncJobRunner when:**
- A job's result is needed immediately (request-response pattern)
- The job is fast enough not to block the caller
- Simple, single-threaded job execution is sufficient
- Testing or development scenarios where queuing overhead is unnecessary

**Characteristics:**
- Blocking execution: caller waits for job completion
- No queue, persistence, or retry mechanism
- Result available immediately
- Suitable for synchronous request handlers (e.g., handling an HTTP request)

**Example:** Processing a cache invalidation synchronously within a request
handler so the response sees the fresh data.

### Queued Runner: Asynchronous Execution

A queued runner (not yet fully implemented in this module) executes jobs
asynchronously through a `QueueBackend`, decoupling job submission from
execution. Jobs are enqueued via `QueueBackend.enqueue(payload)`, persisted
or stored in a message broker (Redis, RabbitMQ, etc.), and processed by
separate worker processes that dequeue jobs via `QueueBackend.dequeue()`.

**Use a queued runner when:**
- Job latency is acceptable and the caller doesn't need the result immediately
- Jobs are long-running or resource-intensive (sending emails, heavy indexing)
- Multiple workers should process jobs in parallel across machines
- Jobs should persist across restarts (via durable queue backends)
- Retry and failure recovery policies are important

**Characteristics:**
- Non-blocking submission: caller enqueues and returns immediately
- Persistent storage: jobs survive process crashes
- Scalable: multiple workers can process jobs in parallel
- Retry-friendly: failed jobs can be retried from the queue
- Suitable for background processing (e.g., full-text search indexing)

**Example:** Queueing a full-text search index update when a document is saved,
processed by background workers without delaying the save response.

**Queue Backends:**
- `QueueBackend` (`queue_backend.py`) is the abstract interface: `enqueue()`,
  `dequeue()`, and `size()`, all async. Concrete implementations are provided
  for RQ (Redis Queue) and Celery.
- `RQQueueBackend` (`rq_backend.py`) adapts RQ (Redis-backed job queue).
- `CeleryQueueBackend` (`celery_backend.py`) adapts Celery (message broker-based
  job queue).

### Design: Separation of Concerns

`SyncJobRunner` and queued runners are designed to share the same handler and
payload contracts (`JobHandler`, `JobPayload`, `JobResult`, `JobAuditEvent`),
allowing a handler to run either synchronously or queued without modification.
The execution model is chosen at runtime (e.g., by the request handler or job
submission point), not by the handler itself. This allows switching between
sync and queued execution without changing handler or payload code.

`QueueBackend` and `SyncJobRunner` are independent concerns:
- `SyncJobRunner` knows nothing about queuing; it only runs a handler once.
- A queued runner (in a later task) will use `QueueBackend` for persistence and
  pair `SyncJobRunner` with a worker loop: dequeue → run → record → retry/dead-letter.

Both models record audit events (`JobAuditEvent`) on completion, enabling
observability regardless of execution mode.

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

`QueueBackend` (`queue_backend.py`) is the interface a job queue backend
must implement: `enqueue(payload)` to append a `JobPayload`, `dequeue()` to
pop and return the next payload in FIFO order (or `None` when the queue is
empty), and `size()` to report how many payloads remain queued. All three
methods are async, mirroring `CacheBackend` and `SearchAdapter`, since real
backends (message brokers, Redis, etc.) are I/O-bound. This is an interface
only, with no in-memory or storage-backed implementation yet; wiring the
queue into `SyncJobRunner` / `JobRegistry` and adding a concrete backend are
left to a later task.

`JobAuditRecorder` (`audit_recorder.py`) is the service that creates and
accumulates `JobAuditEvent`s in memory. `record_job_succeeded(job_type)`
builds a `JobAuditEvent` with a generated `id`, `action=JOB_SUCCEEDED`, and
`occurred_at` set to the current UTC time, appends it, and returns it.
`record_job_failed(job_type, error)` does the same with `action=JOB_FAILED`
and the given `error`. `events()` returns a copy of the recorded events in
order. `SyncJobRunner` (`runner.py`) is constructed with an optional
`audit_recorder` (defaulting to a new `JobAuditRecorder()`) and records an
event on every `run()` outcome: `record_job_succeeded(job_type=payload.job_type)`
when the handler returns a successful `JobResult`, or
`record_job_failed(job_type=payload.job_type, error=result.error)` when
`run()` produces a `FAILED` outcome, whether the handler returned a failed
`JobResult` or raised an exception. Persisting events to storage is left to
a later task.

## QA Checklist

로드맵 **Jobs and Indexing MVP** 범위 — background job abstraction, sync
runner, retries, and indexing jobs — 가 회귀 없이 동작하는지 확인하기 위한
체크리스트다. 이 Phase에 속한 태스크를 새로 추가·수정한 뒤, 또는 커밋 전
`scripts/qa.sh`와는 별개로 job 동작 자체를 사람이 다시 훑어볼 때 사용한다.

각 항목은 "무엇을 확인하는가"와 "어떤 자동화 테스트가 이미 이를 커버하는가"를
함께 적는다. 자동화 테스트가 있다고 해서 항목을 건너뛰어도 된다는 뜻은
아니다 — 새 규칙/모듈을 추가할 때 아래 동작 각각이 여전히 성립하는지 의도를
가지고 재확인하라는 목적이다.

### 사용법

```bash
.venv/bin/python -m pytest tests/modules/jobs -v
```

위 명령으로 아래 체크리스트가 참조하는 테스트를 한 번에 실행할 수 있다.
개별 실행 후에는 반드시 `scripts/test.sh`와 `scripts/qa.sh`도 통과해야 한다.

### 1. Core job interfaces

- [ ] `JobPayload`는 추상 기본 클래스이고, `job_type` 속성은 구현체에서
      정의한 `job_type` 상수를 반환한다. See `test_payload.py::TestJobPayloadJobType`.
- [ ] `JobHandler`는 추상 기본 클래스이고, `handle(payload)` 메서드는 하나의
      `JobPayload`를 받아 `JobResult`를 반환한다. See `test_handler.py`.
- [ ] `JobStatus`는 `PENDING`, `SUCCEEDED`, `FAILED` 열거형이고, 각 상태는
      정확히 구분된다. See `test_status.py`.
- [ ] `JobResult.ok(data=None)`은 `JobStatus.SUCCEEDED` 상태의 결과를 생성하고,
      `JobResult.fail(error)`은 `JobStatus.FAILED` 상태의 결과를 생성한다. See
      `test_result.py::TestJobResultConstruction`.
- [ ] `JobResult`는 성공 시 error 필드를 갖지 않고, 실패 시 error를 필수로
      포함한다. See `test_result.py::TestJobResultErrorHandling`.

### 2. SyncJobRunner

- [ ] `SyncJobRunner.run(handler, payload)`는 `handler.handle(payload)`를
      직접 호출하고 결과를 `JobRunOutcome`으로 감싸서 반환한다. See
      `test_runner.py::TestSyncJobRunnerSuccessfulExecution`.
- [ ] 핸들러가 성공 결과를 반환하면 `JobRunOutcome`의 상태는 `SUCCEEDED`이다.
      See `test_runner.py::TestSyncJobRunnerSuccessfulExecution`.
- [ ] 핸들러가 실패 결과를 반환하면 `JobRunOutcome`의 상태는 `FAILED`이고,
      error는 결과의 error를 그대로 전달한다. See
      `test_runner.py::TestSyncJobRunnerFailedHandlerResult`.
- [ ] 핸들러가 예외를 던지면 `SyncJobRunner`는 이를 catch하여
      `JobStatus.FAILED`인 `JobRunOutcome`으로 변환한다. See
      `test_runner.py::TestSyncJobRunnerCatchesHandlerException`.
- [ ] `SyncJobRunner`에 `audit_recorder`를 전달하면, `run()` 후 성공/실패
      이벤트가 정확히 하나씩 기록된다. See
      `test_runner.py::TestSyncJobRunnerAuditRecording`.

### 3. Job Registry

- [ ] `JobRegistry.register(handler)`는 `handler.job_type`을 키로 하는
      핸들러를 등록한다. See `test_registry.py::TestJobRegistryRegister`.
- [ ] 등록된 핸들러는 `registry.get(job_type)`으로 조회할 수 있다. See
      `test_registry.py::TestJobRegistryRegister::test_register_makes_handler_retrievable`.
- [ ] 같은 `job_type`으로 두 번 등록하려 하면 `DuplicateJobTypeError`가
      발생한다. See `test_registry.py::TestJobRegistryDuplicateRegistration`.
- [ ] 등록되지 않은 `job_type`을 조회하면 `UnknownJobTypeError`가 발생한다.
      See `test_registry.py::TestJobRegistryLookup`.
- [ ] `JobRegistry`의 각 인스턴스는 독립적인 등록 목록을 유지한다. See
      `test_registry.py::TestJobRegistryMultipleInstances`.

### 4. Cache purge job

- [ ] `CachePurgeJobPayload(source="...", parser_version="...")` 생성 시
      source는 빈 문자열이나 공백만으로 거부된다. See
      `test_cache_purge_payload.py::TestCachePurgeJobPayloadConstruction`.
- [ ] `CachePurgeJobPayload(purge_all=True)` 생성 시 source 없이도 페이로드가
      생성되며, 제공된 source가 있어도 무시된다. See
      `test_cache_purge_payload.py::TestCachePurgeJobPayloadConstruction`.
- [ ] `CachePurgeJobPayload.job_type`은 `"cache.purge"`이다. See
      `test_cache_purge_payload.py::TestCachePurgeJobPayloadJobType`.
- [ ] `CachePurgeJobHandler.handle(payload)`는 `purge_all=False`일 때
      `cache.invalidate_render_cache(source, parser_version)`를 호출한다. See
      `test_cache_purge_handler.py::TestCachePurgeJobHandlerScopedPurge`.
- [ ] `CachePurgeJobHandler.handle(payload)`는 `purge_all=True`일 때
      `cache.clear_all()`을 호출한다. See
      `test_cache_purge_handler.py::TestCachePurgeJobHandlerPurgeAll`.
- [ ] 핸들러가 `CachePurgeJobPayload`가 아닌 다른 타입의 페이로드를 받으면
      실패 결과를 반환한다. See `test_cache_purge_handler.py::TestCachePurgeJobHandlerPayloadValidation`.

### 5. Search indexing job

- [ ] `SearchIndexJobHandler.handle(payload)`는
      `IndexDocumentJobPayload`를 받아 `search_adapter.index(search_document)`를
      호출한다. See `test_search_index_handler.py`.
- [ ] 페이로드의 모든 필드가 `SearchDocument`로 올바르게 변환된다. See
      `test_search_index_handler.py::TestSearchIndexJobHandlerIndexing`.
- [ ] 핸들러가 `IndexDocumentJobPayload`가 아닌 다른 타입의 페이로드를 받으면
      실패 결과를 반환한다. See
      `test_search_index_handler.py::TestSearchIndexJobHandlerPayloadValidation`.

### 6. Backlink refresh job

- [ ] `BacklinkRefreshJobPayload(page_name="...")`는 page_name이 빈 문자열이나
      공백만으로 거부된다. See
      `test_backlink_refresh_payload.py::TestBacklinkRefreshJobPayloadConstruction`.
- [ ] `BacklinkRefreshJobPayload.job_type`은 `"backlink.refresh"`이다. See
      `test_backlink_refresh_payload.py::TestBacklinkRefreshJobPayloadJobType`.
- [ ] `BacklinkRefreshJobHandler.handle(payload)`는 페이로드의 page_name을
      검증하고, `JobResult.ok(data={"page_name": ...})`을 반환한다. 실제
      백링크 갱신 로직은 backlinks 모듈이 존재하는 후속 태스크에서
      구현된다. See `test_backlink_refresh_handler.py`.

### 7. Category refresh job

- [ ] `CategoryRefreshJobPayload(category_name="...")`는 category_name이 빈
      문자열이나 공백만으로 거부된다. See
      `test_category_refresh_payload.py::TestCategoryRefreshJobPayloadConstruction`.
- [ ] `CategoryRefreshJobPayload.job_type`은 `"category.refresh"`이다. See
      `test_category_refresh_payload.py::TestCategoryRefreshJobPayloadJobType`.
- [ ] `CategoryRefreshJobHandler.handle(payload)`는 페이로드의 category_name을
      검증하고, `JobResult.ok(data={"category_name": ...})`을 반환한다. 실제
      카테고리 갱신 로직은 categories 모듈이 존재하는 후속 태스크에서
      구현된다. See `test_category_refresh_handler.py`.

### 8. Recent changes job

- [ ] `RecentChangesJobPayload`는 `page_name`, `author_id`, `occurred_at`를
      필수로 요구하며, 이들이 비어있으면 생성할 수 없다. See
      `test_recent_changes_payload.py::TestRecentChangesJobPayloadConstruction`.
- [ ] `RecentChangesJobPayload.job_type`은 `"recent_changes.record"`이다. See
      `test_recent_changes_payload.py::TestRecentChangesJobPayloadJobType`.
- [ ] `RecentChangesJobHandler.handle(payload)`는 페이로드를 검증하고,
      `JobResult.ok(data={...})`을 반환한다. 실제 recent changes 기록 로직은
      후속 태스크에서 구현된다. See `test_recent_changes_handler.py`.

### 9. Job audit events

- [ ] `JobAuditEvent`는 `id`, `action`, `job_type`, `occurred_at`를 필수로
      요구한다. See `test_audit_event.py::TestJobAuditEventConstruction`.
- [ ] `action`이 `JOB_FAILED`이면 `error`는 필수이고, `JOB_SUCCEEDED`이면
      `error`는 금지된다. See `test_audit_event.py::TestJobAuditEventErrorRequirement`.
- [ ] `JobAuditEvent.is_succeeded()` / `is_failed()`는 action을 반영한다. See
      `test_audit_event.py::TestJobAuditEventStatusMethods`.
- [ ] `JobAuditRecorder.record_job_succeeded(job_type)`은 `action=JOB_SUCCEEDED`인
      이벤트를 생성하고, `occurred_at`은 현재 UTC 시간으로 설정된다. See
      `test_audit_recorder.py::TestJobAuditRecorderSuccessRecording`.
- [ ] `JobAuditRecorder.record_job_failed(job_type, error)`는
      `action=JOB_FAILED`인 이벤트를 생성하고 주어진 error를 포함한다. See
      `test_audit_recorder.py::TestJobAuditRecorderFailureRecording`.
- [ ] `JobAuditRecorder.events()`는 기록된 이벤트의 copy를 등록 순서대로
      반환한다. See `test_audit_recorder.py::TestJobAuditRecorderEventsOrdering`.

### 10. Retry policy

- [ ] `RetryPolicy`는 최대 재시도 횟수, 초기 지연, 백오프 인수를 정의한다. See
      `test_retry_policy.py`.
- [ ] `RetryPolicy.should_retry(attempt)`는 시도 횟수가 최대값 이하이면
      True를 반환한다. See `test_retry_policy.py::TestRetryPolicyShouldRetry`.
- [ ] `RetryPolicy.delay_ms(attempt)`는 attempt별로 지수 백오프 지연을
      계산한다. See `test_retry_policy.py::TestRetryPolicyDelayCalculation`.

### 11. Dead letter handling

- [ ] `DeadLetter`는 실패한 잡의 메타데이터를 기록한다: `id`, `payload`,
      `job_type`, `attempt`, `error`, `last_failed_at`. See `test_dead_letter.py`.
- [ ] `DeadLetter.is_beyond_max_retries(retry_policy)`는 시도 횟수가 정책의
      최대값을 초과하면 True를 반환한다. See `test_dead_letter_max_retries.py`.

### 12. Queue backend interface

- [ ] `QueueBackend.enqueue(payload)`는 `JobPayload`를 큐에 추가한다. See
      `test_queue_backend.py`.
- [ ] `QueueBackend.dequeue()`는 다음 `JobPayload`를 FIFO 순서로 반환하거나
      큐가 비어있으면 None을 반환한다. See `test_queue_backend.py`.
- [ ] `QueueBackend.size()`는 큐에 남은 페이로드의 개수를 반환한다. See
      `test_queue_backend.py`.
- [ ] `RQQueueBackend`는 Redis Queue 클라이언트로 job을 enqueue/dequeue한다.
      See `test_rq_backend.py`.
- [ ] `CeleryQueueBackend`는 Celery 클라이언트로 job을 enqueue/dequeue한다.
      See `test_celery_backend.py`.

### 13. Job run context & timeout config

- [ ] `JobRunContext`는 job 실행 중 필요한 메타데이터를 제공한다. See
      `test_job_run_context.py`.
- [ ] `TimeoutConfig`는 job 타입별 타임아웃 값을 정의한다. See
      `test_timeout_config.py`.

### 14. Job metrics hook

- [ ] `JobMetricsHook`는 job 실행 결과를 기록할 수 있는 플레이스홀더다. See
      `test_job_metrics_hook.py`.

### 15. Job fixtures

- [ ] `JobFixtureSet`는 다양한 job 타입을 테스트하기 위한 fixture 데이터를
      제공한다. See `test_fixture_set.py` (또는 관련 fixture 파일).

### 16. Package exports

- [ ] 메인 모듈의 `__init__.py`는 공개 인터페이스를 정의하고, 주요 클래스와
      상수들을 export한다. See `test_package_exports.py`.

### 이 체크리스트가 다루지 않는 것

- 실제 Redis/RabbitMQ 브로커 배포 — queue backend adapters는 골격 상태이며
  프로덕션 통합은 후속 태스크에서 다룬다.
- Queued runner 구현 — `QueueBackend`는 인터페이스만 정의되어 있고, 실제
  dequeue→run→record→retry 루프는 후속 태스크에서 구현된다.
- 감사 이벤트 저장소 — `JobAuditEvent`는 메모리에만 축적되며, DB 저장은
  후속 태스크에서 다룬다.
- Job 성능/부하 특성 — 이 체크리스트는 기능적 정확성만 다룬다.
