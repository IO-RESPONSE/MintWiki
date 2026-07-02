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

## Background Work Boundaries

The jobs module defines clear architectural boundaries to manage dependencies
and responsibilities between the jobs framework and the modules that use it.

### Module Integration Boundary

**Enqueuers (e.g., document module)** decide *what* work needs to happen:
- When a document is edited, the document module knows that search indexing,
  cache invalidation, and recent-changes tracking are needed
- Rather than directly performing this work, the document module creates
  `JobPayload` objects (e.g., `IndexDocumentJobPayload`, `CachePurgeJobPayload`)
  and enqueues them via `QueueBackend.enqueue()`
- This decouples the document module from knowing *how* indexing or cache
  purging actually works

**Jobs framework** (this module) manages *when* and *how often*:
- Persisting payloads in a durable queue
- Executing payloads via registered handlers
- Recording audit events for success/failure
- Retrying failed jobs according to retry policies
- Handling dead letters for jobs that fail beyond max retries

**Handlers** (implemented by subject-matter modules) execute the work:
- The search module provides `SearchIndexJobHandler` that knows how to index
  a document
- The cache module provides `CachePurgeJobHandler` that knows how to purge
  the render cache
- Handlers are *not* responsible for retrying, enqueueing, or persistence;
  those concerns are owned by the jobs framework

### Enqueue vs Execute Boundary

**Enqueue time** (synchronous, blocking):
- The enqueuer has all the data needed to create a payload
- `QueueBackend.enqueue(payload)` stores the payload for later execution
- The enqueuer doesn't know whether the job will run immediately (sync runner)
  or much later (queued runner)
- The enqueue operation should be fast and should not block on the actual
  work (indexing, cache purge, etc.)

**Execute time** (asynchronous, background):
- A job runner (sync or queued) calls `handler.handle(payload)` with the
  stored payload
- The handler performs the actual work, which may be slow or I/O-intensive
- The runner records an audit event on completion
- If a retry policy allows, the runner may retry failed jobs
- The enqueuer is not aware of execution timing or outcomes (unless audit
  events are persisted and the enqueuer queries them separately)

### Handler Design Boundary

**What a handler must do:**
1. Accept a `JobPayload` and return a `JobResult`
2. Be idempotent: calling `handle(payload)` multiple times with the same
   payload must produce the same outcome (important for retries)
3. Validate its payload type; return `JobResult.fail()` if given a payload
   it doesn't recognize
4. Return a `JobResult.ok()` or `JobResult.fail()` to indicate success or
   failure; do not raise uncaught exceptions (the runner will catch and
   convert them, but explicit failures are preferred)

**What the handler *does not* manage:**
1. Retries — the runner or retry policy decides whether to retry
2. Async execution — handler code may be async, but the `handle()` method
   signature is synchronous; wrap async calls in `asyncio.run()` if needed
3. Persistence — the payload is already persisted by the time the handler
   runs; the handler should not be responsible for storing results
4. Audit recording — the runner records audit events automatically

### In-Scope vs Out-of-Scope Boundaries

**Owned by this module (in-scope for MVP):**
- Job payload and handler interfaces
- Sync execution model (`SyncJobRunner`)
- Audit event recording and retrieval from memory
- Retry policy configuration
- Dead letter metadata
- Queue backend abstraction and basic adapters (RQ, Celery)

**Owned by other modules (out-of-scope for MVP):**
- *Handler implementation* — each handler is provided by the module that
  knows how to do the work (cache module, search module, etc.)
- *Worker processes* — actual background workers that dequeue and run jobs
  are deployed separately
- *Persistent audit storage* — audit events are recorded in memory; a later
  phase will persist them to a database
- *Job scheduling* — periodic or delayed job execution (e.g., "run this job
  at 3am") is left to a later phase
- *Monitoring and alerting* — integrating job metrics with observability
  tools is deferred

**Dependencies between modules:**
- The document module depends on the jobs module to enqueue work
- The jobs module depends on handlers provided by other modules (search,
  cache) via the job registry
- The search and cache modules depend on nothing else in the jobs framework;
  they just implement a `JobHandler` interface

## Job Failure Handling

Job failures can occur in two ways:

### Failure Detection

1. **Explicit Failures via JobResult.fail()**

   A handler may return a failed `JobResult` by calling `JobResult.fail(error)`.
   This is the preferred way to indicate a known, recoverable failure. The error
   message provides context for logging and retry decisions.

   Example:
   ```python
   def handle(self, payload: JobPayload) -> JobResult:
       if payload.data is invalid:
           return JobResult.fail("Invalid payload data")
       # ... perform work
       return JobResult.ok()
   ```

2. **Implicit Failures via Exception**

   If a handler raises an exception (e.g., `ValueError`, `RuntimeError`, or any
   other exception), `SyncJobRunner` catches it and automatically converts it to
   a failed `JobResult` with the exception message as the error text. This ensures
   the runner never crashes due to a handler bug; instead, it treats the error as
   a job failure and records an audit event.

   Example:
   ```python
   def handle(self, payload: JobPayload) -> JobResult:
       result = external_service.call()  # may raise exception
       return JobResult.ok(data=result)
   ```

### Failure Representation

All failures are captured in a `JobResult` with:
- `success=False`
- `data=None` (always None for failures)
- `error: str` (required; describes the failure reason)

When `SyncJobRunner.run()` completes, it wraps the `JobResult` in a `JobRunOutcome`:
- `status`: `JobStatus.FAILED` if the result failed
- `result`: the `JobResult` with the error message

This means the caller **always** receives a structured outcome; failures never
propagate uncaught exceptions.

### Failure Recording and Audit Trail

On every job execution (success or failure), `SyncJobRunner` records an audit
event via `JobAuditRecorder`:

- **On Success:** `record_job_succeeded(job_type)` records a `JobAuditEvent`
  with `action=JOB_SUCCEEDED` and `error=None`.

- **On Failure:** `record_job_failed(job_type, error)` records a `JobAuditEvent`
  with `action=JOB_FAILED` and the failure reason. This happens regardless of
  whether the failure came from an explicit `JobResult.fail()` or an exception.

Audit events include:
- `id`: unique identifier generated at record time
- `action`: `JOB_SUCCEEDED` or `JOB_FAILED`
- `job_type`: the payload's job type (for categorizing the failure)
- `occurred_at`: UTC timestamp of the event
- `error`: error message (populated only when `action=JOB_FAILED`)

These events are accumulated in memory and can be persisted to storage in a
later phase. They enable debugging, monitoring, and failure analysis.

### Retry Policies

`RetryPolicy` (`retry_policy.py`) defines when and how a failed job should be
retried:

- `max_attempts`: maximum number of attempts (including the initial attempt).
  For example, `max_attempts=3` means try once, then retry twice.

- `base_delay_seconds`: delay (in seconds) before the first retry.

- `backoff_multiplier`: exponential backoff multiplier (default: 2.0). The delay
  before retry N is calculated as:
  ```
  next_delay(attempt) = base_delay_seconds * (backoff_multiplier ** (attempt - 1))
  ```

  For example, with `base_delay_seconds=1.0` and `backoff_multiplier=2.0`:
  - After attempt 1 (first retry): wait 1.0 second
  - After attempt 2 (second retry): wait 2.0 seconds
  - After attempt 3 (third retry): wait 4.0 seconds

  This pattern ensures transient failures (network glitches, temporary lock
  contention) have time to recover without overwhelming the system with
  immediate retries.

The `RetryPolicy` object itself only computes delay and checks whether retries
remain; the actual retry loop and state transitions are implemented in the
queued runner (a later task).

#### RetryPolicy Usage

`RetryPolicy` is a value object that stores retry configuration and provides
two core methods:

1. **`should_retry(attempt: int) -> bool`**: Determines whether a retry is
   allowed after a given attempt count. Returns `True` if `attempt <
   max_attempts`, `False` otherwise.

   ```python
   policy = RetryPolicy(max_attempts=3, base_delay_seconds=1.0)
   policy.should_retry(1)  # True — can retry after first attempt
   policy.should_retry(2)  # True — can retry after second attempt
   policy.should_retry(3)  # False — max_attempts reached, no more retries
   ```

2. **`next_delay(attempt: int) -> float`**: Computes the wait time (in seconds)
   before the next retry. Uses exponential backoff with the formula:
   ```
   wait_seconds = base_delay_seconds * (backoff_multiplier ^ (attempt - 1))
   ```

   ```python
   policy = RetryPolicy(
       max_attempts=4,
       base_delay_seconds=1.0,
       backoff_multiplier=2.0
   )
   policy.next_delay(1)  # 1.0 seconds (before retry after 1st attempt)
   policy.next_delay(2)  # 2.0 seconds (before retry after 2nd attempt)
   policy.next_delay(3)  # 4.0 seconds (before retry after 3rd attempt)
   ```

#### Common Retry Patterns

**Fast Retries (Transient Network Issues)**
```python
RetryPolicy(
    max_attempts=3,
    base_delay_seconds=0.5,
    backoff_multiplier=2.0
)
```
Waits: 0.5s, 1.0s before giving up. Use for temporary network glitches or
brief service outages.

**Moderate Retries (Service Recovery)**
```python
RetryPolicy(
    max_attempts=4,
    base_delay_seconds=2.0,
    backoff_multiplier=2.0
)
```
Waits: 2s, 4s, 8s before giving up. Use for operations that depend on external
services recovering.

**Long-Running Tasks (Database Lock Contention)**
```python
RetryPolicy(
    max_attempts=5,
    base_delay_seconds=5.0,
    backoff_multiplier=1.5
)
```
Waits: 5s, 7.5s, 11.25s, 16.875s before giving up. Use for heavy operations
that may need time to acquire locks or resources.

**No Backoff (Constant Interval)**
```python
RetryPolicy(
    max_attempts=3,
    base_delay_seconds=2.0,
    backoff_multiplier=1.0
)
```
Waits: 2s, 2s before giving up. Use when you want a fixed retry interval
regardless of attempt count.

#### Retry Policy Best Practices

1. **Choose max_attempts based on failure tolerance**: How many retries is
   acceptable before giving up? For transient errors, 3–5 is typical. For
   resilience-critical jobs, 10+ is reasonable.

2. **Set base_delay_seconds according to recovery time**: If a service is
   down for 2–5 seconds on average, start with `base_delay_seconds=2.0` or
   `3.0`. Immediate retries (`base_delay_seconds=0`) can overwhelm a
   recovering system.

3. **Use exponential backoff for safety**: A `backoff_multiplier` of 2.0 or
   1.5 prevents retry storms that could hammer an overloaded dependency. A
   multiplier of 1.0 is only appropriate when you know fixed-interval retries
   are safe.

4. **Consider the total timeout budget**: With `max_attempts=5`,
   `base_delay_seconds=1.0`, and `backoff_multiplier=2.0`, the worst-case
   total wait is 1 + 2 + 4 + 8 = 15 seconds before all retries are exhausted.
   Ensure this fits your timeout budget (e.g., HTTP request timeout, job
   deadline).

5. **Document why a job retries**: Retries are only useful for transient
   failures. If a failure is permanent (invalid input, missing dependency),
   retries won't help. Use explicit `JobResult.fail()` for permanent errors
   instead of relying on retry exhaustion.

### Dead Letter Handling

`DeadLetter` (`dead_letter.py`) preserves metadata for jobs that fail beyond
the maximum retry attempts:

- `payload`: the original job payload (for inspection and potential replay)
- `job_type`: the job's type (for categorization)
- `error`: the error message from the final failed attempt
- `attempts`: number of attempts made before giving up (always ≥ 1)

When a job's attempt count reaches `retry_policy.max_attempts`, the queued
runner creates a `DeadLetter` and stores it for later analysis or replay.
Dead letters allow operators to:
- Understand why a job failed permanently
- Decide whether the job should be retried manually
- Fix the underlying issue and replay the job
- Collect statistics on failure patterns

Dead letter storage and handling are implemented in a later task.

### Error Handling Best Practices

1. **Return Explicit Failures for Known Issues**

   Use `JobResult.fail()` for validation errors, precondition failures, or
   recoverable business logic errors:
   ```python
   if not await dependency.exists():
       return JobResult.fail("Dependency not found")
   ```

   This makes the failure reason clear in logs and audit events.

2. **Let Exceptions Bubble Up Briefly**

   If a handler calls an external API or system that throws an exception for
   unforeseen reasons (network timeouts, parse errors), allow the exception to
   propagate. `SyncJobRunner` will catch it and convert it to a failed result,
   preserving the exception message:
   ```python
   # SyncJobRunner will catch any exception and return
   # JobResult.fail(str(exception))
   result = external_service.critical_operation()
   return JobResult.ok(data=result)
   ```

3. **Provide Context in Error Messages**

   Error messages should be specific enough to debug failures later:
   ```python
   # Bad: too generic
   return JobResult.fail("Failed")

   # Good: specific context
   return JobResult.fail(
       f"Failed to index page '{page_id}': search adapter returned {status_code}"
   )
   ```

4. **Avoid Swallowing Exceptions Without Logging**

   If you catch an exception in the handler, either return a failed result or
   re-raise it. The audit trail depends on knowing the failure reason.

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
- [ ] `RetryPolicy.next_delay(attempt)`는 attempt별로 지수 백오프 지연을
      계산한다. See `test_retry_policy.py::TestRetryPolicyNextDelay`.

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
