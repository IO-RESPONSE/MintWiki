# cache

Cache abstraction.

Owns cache interfaces, Redis and in-memory backends, key naming, TTL defaults,
and cache observability hooks.

## Cache Invalidation Rules

### 1. Version-Scoped Keys (implicit invalidation)

**Rule**: cache keys are deterministic and derived from `source` content and
`parser_version` (see `build_render_cache_key()` in
`src/modules/cache/key.py`).

- **Format**: `render:v{parser_version}:{sha256(source)}`
- **Effect**: any change to `source` or `parser_version` produces a different
  key, so a lookup with the new value naturally misses the old cached entry.
  No explicit deletion is required for content edits or parser upgrades —
  stale entries for the previous key are simply never read again.

### 2. Explicit Invalidation (`invalidate_render_cache`)

**Rule**: to force a specific `(source, parser_version)` entry to be dropped
immediately, call `invalidate_render_cache(backend, source, parser_version)`
(`src/modules/cache/invalidate.py`).

- **Scope**: deletes only the single cache key computed from the given
  `source` and `parser_version`.
- **Isolation**: does not affect other sources, and does not affect the same
  source cached under a different `parser_version`.
- **Idempotent**: invalidating a key that is missing or already deleted is a
  no-op and never raises.

### 3. Full Cache Clear (`Cache.clear_all()`)

**Rule**: `Cache.clear_all()` removes every cached entry regardless of source
or version, by delegating to the backend's `clear()`.

- `InMemoryCacheBackend.clear()` drops the entire in-memory dict.
- `RedisCacheBackend.clear()` iterates all keys under `key_prefix` with
  `SCAN` (not `KEYS`, to avoid blocking on large keyspaces) and deletes them.
- **Use when**: parser output changes without a `parser_version` bump, or a
  full cold-cache reset is otherwise needed. Prefer bumping `parser_version`
  over a full clear when only some renders are affected, since a version bump
  invalidates precisely and keeps unrelated entries reusable.

### 4. When to Invalidate

- **Document content edited**: no explicit invalidation needed — the new
  `source` string produces a new key automatically (Rule 1).
- **Re-render must be forced for the same source/version** (e.g. reverting a
  bad cached render): call `invalidate_render_cache` with the exact
  `source` and `parser_version` that produced the cached entry.
- **Parser behavior changes release-wide**: bump `parser_version` so future
  lookups miss old entries (Rule 1); use `clear_all()` only if old entries
  must also be actively purged rather than left to age out.

## Testing

Cache invalidation rules are tested in:

- `tests/modules/cache/test_invalidate.py` — explicit invalidation, isolation
  by source and parser version, idempotency
- `tests/modules/cache/test_cache.py` — key derivation, delete, and
  `clear_all` behavior
- `tests/modules/cache/test_backend.py` and `test_redis.py` — per-backend
  `delete`/`clear` semantics
