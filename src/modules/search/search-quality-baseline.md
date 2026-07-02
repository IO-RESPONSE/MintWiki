# Search Quality Baseline

This document records the search quality characteristics of the current
`search` module implementation, as of the Search MVP phase (in-memory
fallback adapter only, no external engine wired in). It exists so later
tasks that improve ranking, tokenization, or Korean-specific matching have
a concrete "before" state to compare against, rather than relying on
intuition about what changed.

This is a snapshot, not a target. It documents what the module does today,
not what it should eventually do — see
[`docs/search-adapter-design.md`](../../../docs/search-adapter-design.md)
for the target design.

## Scope of this baseline

The baseline describes `InMemorySearchAdapter` (`in_memory_adapter.py`),
the only adapter with a working implementation today. `MeilisearchSearchAdapter`
and `OpenSearchSearchAdapter` are skeletons (see `README.md`) and are out of
scope until they have real implementations.

## Current matching behavior

- **Matching strategy**: case-insensitive substring match. A query term
  matches a document if it appears anywhere in the document's `title`,
  `body`, `redirect_target` (when set), or any entry in `categories`.
- **No ranking**: every match gets the same `score` of `1.0`
  (see `SearchResult`). Result order reflects index insertion order, not
  relevance.
- **No tokenization**: there is no word splitting, stemming, or n-gram
  indexing. A multi-word query (e.g. `"apple pie"`) only matches documents
  where that exact substring appears.
- **No Korean-specific handling**: `normalize_korean_text` (Unicode NFC
  composition) exists but is not yet wired into the adapter, so Korean text
  is matched as raw substrings with no josa/eomi stripping or 초성 search.
- **No typo tolerance**: an exact substring is required; there is no
  fuzzy/typo-tolerant matching.

## Baseline results over the fixture corpus

`SearchFixtureLoader` (`fixtures.py`) provides a small, stable document set
used as the reference corpus for this baseline. Indexing every fixture
document into a fresh `InMemorySearchAdapter` and running the queries below
produces the following results (`document_id`s of matches, all with
`score == 1.0`):

| Query           | Matching fixture document(s)                    |
|-----------------|--------------------------------------------------|
| `hello`         | `fixture-title-only`                              |
| `apple`         | `fixture-title-and-body`                          |
| `recipe`        | `fixture-title-and-body`                          |
| `old title`     | `fixture-redirect` (title match)                  |
| `new title`     | `fixture-redirect` (redirect target match)        |
| `documentation` | `fixture-categorized`, `fixture-full`             |
| `wiki`          | `fixture-categorized`                             |
| `search`        | `fixture-full`                                    |
| `nonexistent`   | *(no matches)*                                    |

`tests/modules/search/test_quality_baseline.py` pins this table as an
executable regression test. If a later change to matching, ranking, or
normalization alters any of these results, that test will fail — which is
expected when the change is intentional (update the table and the test
together), and a signal worth double-checking when it isn't.
