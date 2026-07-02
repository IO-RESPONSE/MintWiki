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

`router` (`router.py`) is an empty `APIRouter` skeleton, not yet registered
in `main.py`. Actual search/index HTTP routes are wired up in later tasks.
