# search

Search indexing and query adapters.

Owns title search, body search, redirect search, indexing payloads, and external
search engine integration behind a stable interface.

`SearchAdapter` (`adapter.py`) is the abstract interface concrete adapters
(local fallback, external search engines) implement: `index()` to add or
update a document, `search()` to run a query and return results, `delete()`
to remove a document from the index by id, and `health_check()` to report
whether the search backend is able to serve requests.

`InMemorySearchAdapter` (`in_memory_adapter.py`) is the local fallback
implementation: it keeps indexed `SearchDocument`s in a dict and matches a
query against the title, body, redirect target, or categories with a
case-insensitive substring check. `delete()` removes an entry by id and is a
no-op if the id isn't indexed. Matches are paginated according to the
query's `offset`/`limit` before being returned. `health_check()` always
returns `True` since it has no external dependency to fail.

`MeilisearchSearchAdapter` (`meilisearch_adapter.py`) is a skeleton for an
external Meilisearch-backed adapter: it implements the `SearchAdapter`
interface shape only. Its constructor stores connection settings (`host`,
`index_name`, optional `api_key`) for a future Meilisearch client, but
`index()`, `search()`, `delete()`, and `health_check()` all raise
`NotImplementedError`. The actual Meilisearch client integration and wiring
through `SearchAdapterConfig` are filled in by later tasks.

`OpenSearchSearchAdapter` (`opensearch_adapter.py`) is a skeleton for an
external OpenSearch-backed adapter: it implements the `SearchAdapter`
interface shape only. Its constructor stores connection settings (`host`,
`index_name`, optional `api_key`) for a future OpenSearch client, but
`index()`, `search()`, `delete()`, and `health_check()` all raise
`NotImplementedError`. The actual OpenSearch client integration and wiring
through `SearchAdapterConfig` are filled in by later tasks.

`SearchQuery` (`query.py`) carries the search term plus pagination
parameters: `limit` (max results to return, `None` means no limit) and
`offset` (results to skip, defaults to `0`). `limit` below `1` raises
`InvalidSearchQueryLimitError`; a negative `offset` raises
`InvalidSearchQueryOffsetError`.

`SearchService` (`service.py`) is the service-layer skeleton other modules
depend on: it wraps a `SearchAdapter` and delegates `index_document()`,
`search()`, `delete_document()`, and `health_check()` to it. Converting
source documents into `SearchDocument`s and ranking query results are filled
in by later tasks.

`IndexDocumentRequest` (`schema.py`) is the indexing payload model: it
mirrors the fields needed to construct a `SearchDocument` (`document_id`,
`title`, `body`, `redirect_target`, `categories`) so a future indexing HTTP
route can accept it directly as a request body. It is not yet wired to a
route.

`IndexDocumentJobPayload` (`job_payload.py`) is the document indexing job
payload: it mirrors the same fields as `IndexDocumentRequest`
(`document_id`, `title`, `body`, `redirect_target`, `categories`) but is
meant for a background indexing job queue rather than an HTTP request body.
Unlike `IndexDocumentRequest`, it is a plain domain class (no `pydantic`)
that delegates field validation to `SearchDocument`, keeping the job
payload framework-free per the portability layering rules. Its
`to_search_document()` method returns the underlying `SearchDocument` so a
future job handler can hand it straight to a `SearchAdapter`. It also
carries an `index_version` field, defaulting to the package's
`SEARCH_INDEX_VERSION` constant, so a job handler can tell which index
schema version a queued job targets. The `jobs` module's shared job
payload base class and the actual job handler are added in later tasks;
this payload is defined standalone here in the meantime.

`SearchReindexCommand` (`reindex.py`) is the search reindex command
skeleton: it wraps a `SearchService` and a `document_source` (any iterable
of `SearchDocument`), and its `run()` method iterates the source, indexing
each document through the service, and returns the count of documents
indexed. Wiring `document_source` to pull the live document set from the
`document` module (rather than an iterable passed in directly by the
caller) is filled in by a later task; this command only provides the loop
and delegation shape.

`SearchAdapterConfig` (`config.py`) selects which `SearchAdapter`
implementation to construct: a plain domain class (no `pydantic`, per the
portability layering rules, since it's not a `router.py`/`repository.py`/
`schema.py`) with a `backend` attribute. `backend` defaults to `"in_memory"`,
can be overridden via the `WIKI_SEARCH_BACKEND` environment variable, or
passed explicitly to the constructor (which takes precedence over the
environment variable). Only `"in_memory"` is a valid value today since
`InMemorySearchAdapter` is the only implementation; an unsupported value
raises `InvalidSearchAdapterBackendError`. `meilisearch`/`opensearch`
backends are added, along with the wiring that reads this config to build
the adapter, in later tasks.

`normalize_korean_text` (`normalization.py`) is a Korean text normalization
placeholder: it currently only applies Unicode NFC normalization, composing
decomposed Hangul jamo (initial/medial/final consonants entered as separate
characters) into precomposed syllables so comparisons are consistent across
adapters. It is not yet wired into `InMemorySearchAdapter` or any other
adapter. Real Korean-specific normalization (josa/eomi stripping, initial
consonant (초성) search support, etc.) is filled in by later tasks.

`highlight_search_term` (`highlighting.py`) is a search result highlighting
placeholder: it wraps every case-insensitive substring match of a query term
in a body of text with `<mark>` tags, using the same case-insensitive
substring matching rule `InMemorySearchAdapter` uses to decide matches.
Matched text keeps its original casing; an empty term or text with no match
is returned unchanged. It is not yet wired into `SearchResult`,
`SearchService`, or the router. Snippet extraction (trimming long bodies
down to the matched context), multi-term highlighting, and morphological
match support are filled in by later tasks.

`build_search_cache_key` (`cache_key.py`) is a search result cache key
builder, following the same version-scoped derivation as
`build_render_cache_key` in `modules/cache/key.py`: it combines a search
`term`, `limit`, `offset`, and the `SEARCH_INDEX_VERSION` package constant
(or an explicit `index_version` override) into a deterministic
`"search:v{index_version}:{sha256 hash}"` string, so any change to the
query parameters or a bump to the index schema version naturally produces a
different key. It is not yet wired into `SearchService`, the router, or the
`cache` module's backends — an actual search result cache is added by a
later task.

`SearchMetricsHook` (`metrics.py`) is a search metrics hook placeholder: its
`record_search(term, result_count)` method appends a `SearchMetricsEvent`
(`term`, `result_count`) to an in-memory `events` list on the instance,
rather than sending anything to a real observability backend (Prometheus,
StatsD, etc.). It is not yet called from `SearchService` or the router;
that wiring, along with real metrics backend integration, is filled in by
a later task.

`SearchFixtureLoader` (`fixtures.py`) provides a small set of reusable
`SearchDocument` fixture documents for adapter/service/reindex tests:
title-only, title+body, redirect, categorized, and a "full" document with
title/body/categories together. `load_all()` returns every fixture
document; `load_by_id(document_id)` looks one up by its fixture id and
raises `ValueError` for an unknown id.

`SearchServiceError` (`errors.py`) is the search service error handling
model: it wraps an exception raised by a `SearchAdapter` implementation
(e.g. an external search engine client) together with the name of the
operation that failed (`index`, `search`, or `delete`), so callers can
handle a single error type regardless of which adapter is in use. It stores
`operation` and `original_error` and formats both into the exception
message. `SearchService` does not yet catch adapter exceptions and raise
this error in their place; that mapping is filled in by a later task.

`router` (`router.py`) is an `APIRouter`, not yet registered in `main.py`.
It exposes `GET /title` and `GET /body`, each reading a required query
parameter (`title` or `body`, respectively) plus optional `limit`/`offset`
pagination parameters, building a `SearchQuery`, and delegating to a
`SearchService` pulled from `request.app.state.search_service` (the app or
test that mounts the router is responsible for setting this). An empty or
whitespace-only query parameter returns `422`. Results are returned as a
`SearchResponse` (see `schema.py`) listing each match's `document_id`,
`title`, and `score`. It also exposes a `GET /health` route placeholder that
delegates to `SearchService.health_check()` and returns a
`SearchHealthResponse` (`{"healthy": true/false}`); it always responds `200`
and does not yet map backend failures to a distinct HTTP status code (e.g.
`503`) or handle a raised `SearchServiceError` — both are filled in by later
tasks. Indexing HTTP routes are wired up in later tasks.

## External Search Engine Choice

No external search engine has been selected as the production backend yet,
and none is required to be. `SearchAdapterConfig` (`config.py`) only accepts
`"in_memory"` today (`ALLOWED_SEARCH_ADAPTER_BACKENDS`); `InMemorySearchAdapter`
is both the current default and the local fallback that keeps the module
usable with zero external dependencies.

`MeilisearchSearchAdapter` and `OpenSearchSearchAdapter` exist side by side as
skeletons (see above) because the module deliberately keeps the choice open
between them rather than committing early. This follows the "hide the engine"
principle in [`docs/search-adapter-design.md`](../../../docs/search-adapter-design.md):
since both engines implement the same `SearchAdapter` interface, callers pay
no cost for the decision being deferred, and either skeleton can be filled in
— or dropped — without touching `SearchService`, the router, or any caller.

When the choice is made (a later task, per the initial stack note in the
top-level [`README.md`](../../../README.md#초기-스택), "adapter first, then
Meilisearch/OpenSearch"), it should weigh:

- **Operational simplicity**: Meilisearch ships as a single self-contained
  binary with minimal configuration; OpenSearch requires a JVM-based cluster
  and more operational overhead.
- **License**: Meilisearch is MIT-licensed; OpenSearch is Apache 2.0
  (a fork of Elasticsearch maintained after Elasticsearch's license change).
- **Relevance and typo tolerance**: Meilisearch has typo-tolerant ranking
  built in by default; OpenSearch relies on standard BM25 plus optional
  plugins and analyzers that must be configured explicitly.
- **CJK/Korean tokenization**: OpenSearch has mature CJK analyzer plugins
  (e.g. `nori`); Meilisearch's tokenizer is simpler and less tunable for
  Korean text.
- **Scale**: OpenSearch is built for large, sharded, multi-node deployments;
  Meilisearch targets small-to-medium single-node deployments.

Whichever engine is picked, extending `ALLOWED_SEARCH_ADAPTER_BACKENDS` and
wiring `SearchAdapterConfig` to construct the corresponding adapter is left
to that later task, as already noted above.

Note this is a separate decision from the longer-term PHP portability path
described in `docs/search-adapter-design.md`, which targets pure-PHP
TNTSearch for the eventual PHP/MariaDB reimplementation specifically because
that target excludes introducing an extra search service. Meilisearch and
OpenSearch are candidates for this repository's current Python/FastAPI stack
only; they do not change the PHP migration target.

## Search Quality Baseline

[`search-quality-baseline.md`](search-quality-baseline.md) records the
current matching/ranking characteristics of `InMemorySearchAdapter` (plain
substring matching, no ranking, no Korean-specific handling) along with a
table of expected results over the `SearchFixtureLoader` fixture corpus.
`tests/modules/search/test_quality_baseline.py` pins that table as a
regression test, so later quality improvements have a documented "before"
state to compare against.

## Search Phase QA Checklist

Manual/exploratory checklist for the Search MVP phase (search adapter,
local fallback search, indexing contracts), grouped by the same areas
documented above. Each item names the automated test that already covers
it, so a QA pass can spot-check the listed behavior directly (e.g. via the
HTTP API or a REPL) and cross-check against the referenced test when a
result looks wrong.

### Adapter interface & in-memory fallback

- [ ] `SearchAdapter` cannot be instantiated directly and requires
  `index()`/`search()`/`delete()`/`health_check()` on any subclass.
  (`test_adapter.py::TestSearchAdapterInterface`)
- [ ] `InMemorySearchAdapter.search()` matches a query term
  case-insensitively against `title`, `body`, `redirect_target`, and
  `categories`, and never duplicates a document that matches in more than
  one field. (`test_in_memory_adapter.py::TestInMemorySearchAdapterSearch`,
  `::TestInMemorySearchAdapterBodySearchFallback`,
  `::TestInMemorySearchAdapterRedirectSearch`)
- [ ] Re-indexing a `document_id` that is already indexed overwrites the
  stored document (title/body/redirect/categories all updated), rather
  than adding a second entry. (`test_in_memory_adapter.py::TestInMemorySearchAdapterIndex`)
- [ ] `delete()` removes only the target document and is a no-op (does not
  raise) for an id that was never indexed.
  (`test_in_memory_adapter.py::TestInMemorySearchAdapterDelete`)
- [ ] `limit`/`offset` on `SearchQuery` paginate the in-memory result set
  correctly, including an offset past the end of the results.
  (`test_in_memory_adapter.py::TestInMemorySearchAdapterPagination`)
- [ ] `health_check()` always returns `True` for `InMemorySearchAdapter`
  (empty or non-empty index) since it has no external dependency.
  (`test_in_memory_adapter.py::TestInMemorySearchAdapterHealthCheck`)
- [ ] `MeilisearchSearchAdapter`/`OpenSearchSearchAdapter` store their
  connection settings on construction but raise `NotImplementedError` from
  every `SearchAdapter` method — confirm this is expected (skeletons only)
  rather than a bug. (`test_meilisearch_adapter.py`, `test_opensearch_adapter.py`)

### Query & pagination

- [ ] `SearchQuery` rejects an empty or whitespace-only `term`, a `limit`
  below `1`, and a negative `offset`. (`test_query.py`)
- [ ] `SearchQuery` defaults to no limit and `offset == 0` when neither is
  given. (`test_query.py::TestSearchQueryPagination`)

### Service & error mapping

- [ ] `SearchService.index_document()`/`search()`/`delete_document()`/
  `health_check()` delegate straight through to the configured adapter with
  no ranking or filtering of their own. (`test_service.py::TestSearchServiceIndexDocument`,
  `::TestSearchServiceDeleteDocument`, `::TestSearchServiceSearch`)
- [ ] Every `SearchResult` returned by the service carries the same
  placeholder `score` of `1.0`, regardless of where the match occurred —
  confirm this before treating result order as relevance-ranked.
  (`test_service.py::TestSearchServiceRankingPlaceholder`)
- [ ] When the underlying adapter raises, `SearchService` wraps the
  exception in a `SearchServiceError` carrying the failing operation name
  (`index`/`search`/`delete`/`health_check`) and chains the original
  exception as the cause, for all four service methods.
  (`test_service.py::TestSearchServiceAdapterFailureMapping`)

### Indexing payloads & reindex command

- [ ] `IndexDocumentRequest` (schema) and `IndexDocumentJobPayload` both
  require `document_id`/`title` and accept the same optional
  `redirect_target`/`categories` fields. (`test_schema.py`, `test_job_payload.py`)
- [ ] `IndexDocumentJobPayload.to_search_document()` produces a
  `SearchDocument` with all fields carried over, including when only the
  required fields are set. (`test_job_payload.py::TestIndexDocumentJobPayloadToSearchDocument`)
- [ ] `IndexDocumentJobPayload.index_version` defaults to
  `SEARCH_INDEX_VERSION` and can be overridden explicitly.
  (`test_job_payload.py::TestIndexDocumentJobPayloadIndexVersion`)
- [ ] `SearchReindexCommand.run()` indexes every document from its
  `document_source` iterable, returns the count indexed, and makes each
  document searchable afterward; an empty source indexes nothing.
  (`test_reindex.py::TestSearchReindexCommandRun`)
- [ ] A `SearchServiceError` raised mid-reindex propagates out of
  `SearchReindexCommand.run()` rather than being swallowed.
  (`test_reindex.py::test_propagates_search_service_error`)

### Config

- [ ] `SearchAdapterConfig` defaults to `"in_memory"`, can be overridden by
  the `WIKI_SEARCH_BACKEND` environment variable, and an explicit
  constructor argument takes precedence over the environment variable.
  (`test_config.py::TestSearchAdapterConfig`)
- [ ] An unsupported backend value — from either the constructor or the
  environment variable — raises `InvalidSearchAdapterBackendError`.
  (`test_config.py::test_unsupported_backend_raises_error`,
  `::test_unsupported_backend_from_environment_raises_error`)

### Normalization & highlighting (not yet wired in)

- [ ] `normalize_korean_text` only performs Unicode NFC composition — it
  does not strip particles (josa/eomi), trim whitespace, or change case,
  and is idempotent when applied twice. Confirm it is **not** called by
  `InMemorySearchAdapter` yet. (`test_normalization.py::TestNormalizeKoreanTextNoOpBaseline`)
- [ ] `highlight_search_term` wraps every case-insensitive match with
  `<mark>` tags while preserving the original casing of matched text, and
  returns the input unchanged when the term is empty or has no match.
  Confirm it is **not** called from `SearchService`, `SearchResult`, or the
  router yet. (`test_highlighting.py::TestHighlightSearchTerm`)
- [ ] `SearchMetricsHook.record_search()` appends a `SearchMetricsEvent`
  (`term`, `result_count`) to its `events` list in call order, and each hook
  instance has its own independent `events` list. Confirm it is **not**
  called from `SearchService` or the router yet.
  (`test_metrics.py::TestSearchMetricsHookRecordSearch`)

### Fixtures

- [ ] `SearchFixtureLoader.load_all()` returns fixture documents with
  unique `document_id`s covering title-only, title+body, redirect,
  categorized, and "full" scenarios; `load_by_id()` raises `ValueError` for
  an unknown id. (`test_fixtures.py`)

### Router (`GET /title`, `GET /body`, `GET /health`)

- [ ] `GET /title` and `GET /body` return `422` for a missing, empty, or
  whitespace-only query parameter, and apply `limit`/`offset` from the
  request. (`test_router.py::TestSearchByTitle`, `::TestSearchByBody`)
- [ ] Both routes also match against `redirect_target` and `categories`,
  not just the field named in the route path. (`test_router.py::TestSearchMatchesAcrossIndexedFields`)
- [ ] `GET /health` always returns `200` with `{"healthy": true/false}`
  reflecting the adapter's `health_check()` result — confirm it does not
  yet map an unhealthy backend to `503` or catch a raised
  `SearchServiceError`. (`test_router.py::TestSearchHealth`)
- [ ] Response bodies expose only the declared fields (`document_id`,
  `title`, `score`) — no accidental leakage of `body`/`redirect_target`.
  (`test_router.py::TestSearchResponseShape`)

### Quality baseline

- [ ] The fixture-corpus query table in
  [`search-quality-baseline.md`](search-quality-baseline.md) still matches
  what `InMemorySearchAdapter` returns today; a mismatch means either the
  doc or the adapter changed without the other being updated.
  (`test_quality_baseline.py::TestSearchQualityBaseline`)

### What this checklist does not cover

- Real Meilisearch/OpenSearch integration behavior — both adapters are
  skeletons today; actual client wiring is filled in by later tasks.
- Indexing HTTP routes — `IndexDocumentRequest` is defined but not yet
  wired to a route.
- Search performance/load characteristics under real deployment traffic —
  this checklist covers functional correctness only.
