# search

Search indexing and query adapters.

Owns title search, body search, redirect search, indexing payloads, and external
search engine integration behind a stable interface.

`SearchAdapter` (`adapter.py`) is the abstract interface concrete adapters
(local fallback, external search engines) implement: `index()` to add or
update a document, and `search()` to run a query and return results.

`InMemorySearchAdapter` (`in_memory_adapter.py`) is the local fallback
implementation: it keeps indexed `SearchDocument`s in a dict and matches a
query against the title with a case-insensitive substring check. Body
search, redirect resolution, and other indexing fields are handled by
later tasks.
