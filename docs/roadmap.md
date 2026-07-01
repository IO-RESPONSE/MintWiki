# Roadmap

## Phase 0: Blueprint and Runner

- Architecture document
- Module boundaries
- 10-minute job model
- Local git repository scaffold
- systemd runner examples
- bootstrap/test/QA scripts

## Phase 1: Minimal App

- FastAPI app bootstrap
- config loader
- health endpoint
- pytest baseline
- Docker Compose with app and PostgreSQL

## Phase 2: Document Core

- title normalization
- document model
- revision model
- create/read/update flow
- current revision pointer
- edit conflict detection
- recent changes event stub

## Phase 3: Parser and Render

- parser interface
- text escaping
- headings
- links
- bold/italic/strike
- lists
- simple tables
- parser fixtures
- render cache adapter

## Phase 4: ACL

- user identities
- groups
- document ACL rules
- namespace defaults
- permission matrix tests
- protected read/write paths

## Phase 5: Discussion

- discussion thread model
- comments
- thread state
- discussion ACL
- discussion audit logs

## Phase 6: Search and Jobs

- search adapter
- local fallback search
- indexing payloads
- job interface
- sync job runner
- queued backend adapter

## Phase 7: Admin and Operations

- blocks
- protections
- reports
- audit viewer
- cache purge tools
- backup notes
- monitoring hooks

## Phase 8: Hardening

- XSS fixtures
- ACL bypass tests
- parser abuse tests
- rate limit design
- load test scripts
- deployment checklist
