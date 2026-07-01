# Architecture

## Architecture Style

The engine starts as a modular monolith. It runs as one deployable application,
but each domain module owns its models, services, repository interfaces, tests,
and public API routes.

This keeps local development light while preserving a path to split selected
modules later if traffic or operational pressure justifies it.

## Core Principles

- Store source text and rendered output separately.
- Store document revisions append-only whenever possible.
- Treat parsing as a deterministic pipeline that emits HTML plus metadata.
- Extract links, categories, redirects, headings, and transclusions during parse.
- Do expensive work through jobs, with a synchronous fallback for early builds.
- Put ACL checks before every write and every protected read.
- Cache rendered documents and expensive metadata aggressively.
- Keep search as an external index behind an internal adapter.
- Every module must expose a small service interface and hide storage details.

## Runtime Components

```text
Client
  -> Reverse Proxy / CDN
  -> FastAPI App
     -> Document Module
     -> Revision Module
     -> Parser Module
     -> Render Module
     -> ACL Module
     -> Discussion Module
     -> Search Module
     -> User Module
     -> Admin Module
     -> Audit Module
     -> Cache Module
     -> Jobs Module
  -> PostgreSQL
  -> Redis
  -> Search Engine
```

## Request Flow: Document View

1. Normalize the requested title.
2. Check read ACL.
3. Check render cache by document id, revision id, parser version, and viewer mode.
4. If cache hit, return cached HTML and metadata.
5. If cache miss, load current revision.
6. Parse source into an intermediate representation.
7. Render HTML and extract metadata.
8. Store render cache.
9. Return response.

## Request Flow: Document Edit

1. Normalize title.
2. Check edit ACL.
3. Load current revision metadata.
4. Validate edit base revision to detect conflicts.
5. Create a new revision.
6. Update document current revision pointer in the same transaction.
7. Enqueue metadata extraction, search indexing, cache purge, and recent-change jobs.
8. Return new revision id.

## Data Ownership

Each module owns its tables and exposes service methods. Cross-module access
must go through service interfaces unless a read model is explicitly documented.

## Initial Deployment Model

The first deployable shape is Docker Compose:

- app
- postgres
- redis
- search, added after adapter tests exist

Production can add reverse proxy, CDN, workers, monitoring, and replicas without
changing core module boundaries.
