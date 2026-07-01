# Module Design

## app

Owns process bootstrap, configuration loading, dependency injection, route
registration, health checks, and startup validation.

Public surface:

- `GET /health`
- settings object
- database session factory
- module registry

## document

Owns stable document identity and title lifecycle.

Responsibilities:

- title normalization
- document creation
- document lookup
- current revision pointer
- redirects at document level
- document move state
- document delete state

Does not own revision body storage.

## revision

Owns immutable document revisions.

Responsibilities:

- revision creation
- source text storage
- edit summaries
- author attribution
- parent revision tracking
- diff generation
- revert planning

Does not decide whether a user may edit. ACL decides that before revision calls.

## parser

Owns source syntax parsing.

Responsibilities:

- NamuMark-like source tokenization
- block parsing
- inline parsing
- table parsing
- macro recognition
- parser diagnostics
- parse metadata extraction

The parser must not directly read the database.

## render

Owns transformation from parsed document to safe HTML.

Responsibilities:

- HTML generation
- XSS-safe escaping
- URL sanitization
- heading id generation
- table HTML generation
- render cache key construction
- render cache invalidation policy

## acl

Owns permission decisions.

Responsibilities:

- read/edit/discuss/move/delete/admin permission checks
- document-level ACL rules
- namespace-level ACL defaults
- user group rules
- temporary restrictions
- permission matrix tests

Every protected operation must call ACL explicitly.

## discussion

Owns document discussions and thread state.

Responsibilities:

- thread creation
- comments
- thread state changes
- discussion ACL integration
- discussion logs
- hidden/deleted comment metadata

## search

Owns search indexing and query adapters.

Responsibilities:

- title search
- body search
- redirect search
- indexing job payloads
- local fallback search for development
- external search adapter

The initial implementation can use database-backed fallback behind the same
interface.

## cache

Owns cache abstractions, not business rules.

Responsibilities:

- cache interface
- Redis backend
- in-memory backend for tests
- key naming
- TTL defaults
- cache metrics hooks

## jobs

Owns background work orchestration.

Responsibilities:

- job interface
- sync runner for local development
- queued runner adapter
- retry metadata
- dead-letter handling
- job audit records

## user

Owns accounts and sessions.

Responsibilities:

- account model
- password authentication
- session state
- user groups
- user profile basics
- IP identity representation

## admin

Owns administrative workflows.

Responsibilities:

- blocks
- protections
- reports
- moderation actions
- admin dashboards
- operational switches

## audit

Owns immutable event logs.

Responsibilities:

- document logs
- permission change logs
- admin action logs
- auth logs
- job logs
- append-only audit storage

Audit records should be written by modules through a small audit service.

## Dependency Rules

- `document` may call `revision` for current revision details through service interfaces.
- `revision` may call `parser` only in tests or validation helpers, not during storage.
- `render` may call `parser` and `cache`.
- `acl` may call `user`, `document`, and `audit`.
- `discussion` may call `acl`, `user`, and `audit`.
- `search` consumes events from `jobs` or service calls; it should not own edits.
- `admin` may call `acl`, `user`, `document`, `discussion`, and `audit`.
- `audit` should avoid calling business modules.
