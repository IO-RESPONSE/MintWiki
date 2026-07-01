# Wiki Engine Blueprint

This repository is the design and execution scaffold for a new wiki engine.
The target is a modular, lightweight engine inspired by MediaWiki's operating
architecture and shaped around NamuWiki-style user workflows.

The project is intentionally split into small tasks that can be implemented,
tested, and committed in short runner cycles.

## Goals

- Build a new wiki engine, not a MediaWiki plugin.
- Use a modular monolith first, with clean module boundaries.
- Keep the development environment bootstrappable in about 10 minutes.
- Split all implementation into small jobs with explicit acceptance criteria.
- Make every job independently testable by automated QA.

## Initial Stack

- Backend: Python + FastAPI
- Database: PostgreSQL
- Cache: Redis, optional during early local development
- Search: adapter first, Meilisearch/OpenSearch later
- Queue: synchronous fallback first, worker backend later
- Tests: pytest
- Deployment: Docker Compose first
- Scheduler: systemd timer calling a runner script

## Local Environment

Copy `.env.example` to `.env` before local runs, then adjust the placeholder
database and Redis URLs for your local services as needed.

### Bootstrap

Start the local app and PostgreSQL services with Docker Compose:

```bash
docker compose up --build
```

### Testing

Run the test suite locally:

```bash
scripts/test.sh
```

### QA Before Commit

Run the complete local QA workflow to check your changes:

```bash
scripts/qa.sh
```

This runs tests and validates code formatting. QA must pass before committing.

## Repository Layout

```text
docs/              Architecture and module design
tasks/             10-minute job queue
src/app/           Application bootstrap and shared config
src/modules/       Engine modules
tests/             Cross-module tests
scripts/           Bootstrap, test, QA, runner helpers
ops/systemd/       systemd service and timer examples
```

## Current Status

This is the design scaffold. Code modules are placeholders until the first
implementation tasks are executed.
