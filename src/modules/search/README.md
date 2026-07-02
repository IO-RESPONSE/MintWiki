# search

Search indexing and query adapters.

Owns title search, body search, redirect search, indexing payloads, and external
search engine integration behind a stable interface.

`SearchAdapter` (`adapter.py`) is the abstract interface concrete adapters
(local fallback, external search engines) implement: `index()` to add or
update a document, `search()` to run a query and return results, and
`delete()` to remove a document from the index by id.

`InMemorySearchAdapter` (`in_memory_adapter.py`) is the local fallback
implementation: it keeps indexed `SearchDocument`s in a dict and matches a
query against the title, body, redirect target, or categories with a
case-insensitive substring check. `delete()` removes an entry by id and is a
no-op if the id isn't indexed. Matches are paginated according to the
query's `offset`/`limit` before being returned.

`SearchQuery` (`query.py`) carries the search term plus pagination
parameters: `limit` (max results to return, `None` means no limit) and
`offset` (results to skip, defaults to `0`). `limit` below `1` raises
`InvalidSearchQueryLimitError`; a negative `offset` raises
`InvalidSearchQueryOffsetError`.

`SearchService` (`service.py`) is the service-layer skeleton other modules
depend on: it wraps a `SearchAdapter` and delegates `index_document()`,
`search()`, and `delete_document()` to it. Converting source documents into
`SearchDocument`s and ranking query results are filled in by later tasks.

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

`router` (`router.py`) is an `APIRouter`, not yet registered in `main.py`.
It exposes `GET /title` and `GET /body`, each reading a required query
parameter (`title` or `body`, respectively) plus optional `limit`/`offset`
pagination parameters, building a `SearchQuery`, and delegating to a
`SearchService` pulled from `request.app.state.search_service` (the app or
test that mounts the router is responsible for setting this). An empty or
whitespace-only query parameter returns `422`. Results are returned as a
`SearchResponse` (see `schema.py`) listing each match's `document_id`,
`title`, and `score`. Indexing HTTP routes are wired up in later tasks.
