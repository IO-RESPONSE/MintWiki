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
future job handler can hand it straight to a `SearchAdapter`. The `jobs`
module's shared job payload base class and the actual job handler are
added in later tasks; this payload is defined standalone here in the
meantime.

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
`title`, and `score`. Indexing HTTP routes are wired up in later tasks.

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
