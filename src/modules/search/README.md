# search

Search indexing and query adapters.

Owns title search, body search, redirect search, indexing payloads, and external
search engine integration behind a stable interface.

`SearchAdapter` (`adapter.py`) is the abstract interface concrete adapters
(local fallback, external search engines) implement: `index()` to add or
update a document, and `search()` to run a query and return results.

`InMemorySearchAdapter` (`in_memory_adapter.py`) is the local fallback
implementation: it keeps indexed `SearchDocument`s in a dict and matches a
query against the title, body, redirect target, or categories with a
case-insensitive substring check.

`SearchService` (`service.py`) is the service-layer skeleton other modules
depend on: it wraps a `SearchAdapter` and delegates `index_document()` and
`search()` to it. Converting source documents into `SearchDocument`s and
shaping query results (ranking, pagination) are filled in by later tasks.
