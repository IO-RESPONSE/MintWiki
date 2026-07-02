# Search Adapter Design

Engine-neutral design for the `search` module. This document is the reference
for the queued Search MVP tasks (roughly `0241`–`0246` and their tests). A
runner cycle implementing those tasks should follow the contract described
here.

## Purpose

`search` owns title search, body search, redirect search, indexing payloads,
and external engine integration — all **behind a stable interface**. The module
must not commit the rest of the engine to any single search backend.

The concrete long-term target backend is **pure-PHP full-text search
(TNTSearch) with an n-gram tokenizer for Korean/CJK**, chosen because the engine
will be reimplemented in PHP on MariaDB with the constraint that no extra search
service (Elasticsearch, Meilisearch, Manticore, Mroonga, …) may be introduced.
This document keeps the interface neutral enough that the current Python code and
the future PHP code can share one contract.

## Design principle: hide the engine, hide the tokenizer

Two things must never leak out of the `search` module:

1. **The engine.** Nothing outside `search` may know whether results come from an
   in-memory index, a SQL query, or TNTSearch. Callers depend only on
   `SearchAdapter`.
2. **The tokenizer.** How text is split for indexing (n-gram, whitespace, or a
   future morphological analyzer) is an adapter-internal concern. The interface
   speaks in documents and queries, never in tokens.

Rationale for hiding the tokenizer: pure-PHP has no production-grade Korean
morphological analyzer, so the portable choice is **n-gram (bigram) tokenization**
— the same technique `pg_bigm` and the MySQL ngram parser use internally. If the
tokenizer is buried inside the adapter, the engine can start with n-gram and later
adopt a better analyzer without touching a single caller or the domain layer.

## Domain models

Plain domain objects — no framework, no engine types. These belong in the domain
layer and are subject to the portability boundary in
[AGENTS.md](../AGENTS.md#이식성-계층-규칙-portability-layering); they must not
import `fastapi`, `sqlalchemy`, or `pydantic`.

```python
class SearchDocument:
    """검색 색인에 넣을 문서. 엔진 비종속 페이로드."""
    doc_id: str
    title: str
    body: str
    # 리다이렉트·별칭 등 제목 외 매칭 대상 (선택)
    redirects: list[str]
    namespace: str


class SearchQuery:
    """검색 질의. 텍스트와 페이징만 담고, 토크나이징 방식은 명시하지 않는다."""
    text: str
    limit: int
    offset: int


class SearchHit:
    """단일 검색 결과 항목."""
    doc_id: str
    title: str
    # 엔진이 계산한 관련도 점수 (높을수록 관련도 높음)
    score: float


class SearchResult:
    """질의 응답. 순위가 매겨진 결과 목록과 총 개수."""
    hits: list[SearchHit]
    total: int
```

Notes:

- `score` is deliberately a float, not an engine-specific object. An in-memory
  adapter may return simple match counts; TNTSearch returns BM25 scores. Callers
  only rely on ordering (higher = better), never on the absolute value.
- `SearchQuery` carries no tokenizer hint. The adapter decides how to interpret
  `text`.

## Adapter interface (port)

```python
class SearchAdapter(ABC):
    """검색 백엔드 포트. 모든 검색엔진 구현이 이 인터페이스를 만족한다."""

    @abstractmethod
    async def index(self, document: SearchDocument) -> None:
        """문서를 색인한다 (생성 또는 갱신). 토크나이징은 구현 내부에서 처리한다."""

    @abstractmethod
    async def remove(self, doc_id: str) -> None:
        """색인에서 문서를 제거한다. 없는 id면 조용히 무시한다."""

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult:
        """질의를 실행하고 관련도 순으로 정렬된 결과를 반환한다."""
```

Contract rules the runner must honor:

- `index` is idempotent per `doc_id`: indexing the same id twice replaces the
  prior entry, never duplicates it.
- `search` returns hits ordered by `score` descending; ties broken by `title`
  for deterministic tests.
- `remove` on an unknown `doc_id` is a no-op, not an error.
- Title, redirect, and body matches all flow through `search`. Result ranking may
  weight title/redirect matches above body matches, but that weighting is an
  adapter-internal policy, not part of the interface.

## Planned adapters

| Adapter | Task | Backend | Tokenizer | Purpose |
|---|---|---|---|---|
| `InMemorySearchAdapter` | 0246 | Python dict | trivial substring / bigram | tests, local dev, the default fallback |
| (later) DB fallback adapter | later queue | MariaDB/PostgreSQL | PHP/SQL-side n-gram | production before a dedicated engine |
| (future, PHP) `TntSearchAdapter` | post-migration | TNTSearch (pure PHP) | **bigram n-gram** | production search in the PHP engine |

Only `InMemorySearchAdapter` (0246) is in near-term scope. Implement it as the
literal fallback the roadmap calls for: an in-process index that satisfies the
full `SearchAdapter` contract with no external dependency. A simple bigram index
(map each 2-character shingle to the set of doc ids, score by shingle overlap)
is enough to exercise Korean search behavior in tests and mirrors what the PHP
n-gram tokenizer will later do.

## Portability path (Python → PHP)

Because the engine is hidden behind `SearchAdapter`, the PHP migration is local:

1. The domain models (`SearchDocument`, `SearchQuery`, `SearchResult`) translate
   line-by-line to PHP value objects.
2. `SearchAdapter` becomes a PHP `interface`.
3. `InMemorySearchAdapter` translates directly (useful for PHP unit tests too).
4. A new `TntSearchAdapter` implements the same interface over TNTSearch, plugging
   a bigram tokenizer via TNTSearch's `TokenizerInterface`. No caller changes.

The n-gram decision made here means the indexing field design (what text is
tokenized, how titles/redirects are weighted) is settled once and reused across
both languages — the shingle strategy is identical in Python and PHP.

## What stays out of the interface

To keep the boundary durable, the following are explicitly **not** part of
`SearchAdapter` and must live inside a specific adapter (or a later task):

- Tokenizer selection and n-gram size.
- Index storage location (dict, SQLite file, SQL table).
- Relevance tuning knobs (field boosts, BM25 parameters).
- Bulk reindex / index rebuild orchestration (this belongs to the `jobs` module
  via indexing payloads, not to the query-time adapter).
