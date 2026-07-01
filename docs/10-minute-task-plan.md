# 10-Minute Task Plan

This document is the human-readable backlog index. The executable queue is the
set of individual markdown files under `tasks/queue/`.

Each task should be small enough for one unattended runner cycle:

```text
run-next-task.sh -> codex exec -> test -> qa -> commit
```

## Completed

- `0001`: Bootstrap Python app
- `0002`: Add development scripts
- `0003`: Add systemd runner units

## Active Queue: Phase 1

Phase 1 establishes the development foundation.

| Task | Purpose |
|---|---|
| `0004` | Add repository coding rules for Codex |
| `0005` | Add `.env.example` |
| `0006` | Add Dockerfile for app |
| `0007` | Add Docker Compose for app and PostgreSQL |
| `0008` | Add database dependency package metadata |
| `0009` | Add database settings fields |
| `0010` | Add database connection module |
| `0011` | Add migration tool baseline |
| `0012` | Add initial empty migration |
| `0013` | Add CI-like local QA command documentation |
| `0014` | Add title normalization utility |
| `0015` | Add title normalization tests |
| `0016` | Add document module package skeleton |
| `0017` | Add document domain dataclass |
| `0018` | Add document repository interface |
| `0019` | Add in-memory document repository |
| `0020` | Add document service create method |
| `0021` | Add document service get method |
| `0022` | Add document router skeleton |
| `0023` | Add create document API route |
| `0024` | Add get document API route |
| `0025` | Add document API tests |
| `0026` | Add revision module package skeleton |
| `0027` | Add revision domain dataclass |
| `0028` | Add in-memory revision repository |
| `0029` | Connect document create to first revision |
| `0030` | Add current revision read model |

## Next Planned Ranges

These ranges should be expanded into individual queue files before the runner
reaches them.

| Range | Phase |
|---|---|
| `0031-0060` | PostgreSQL persistence for document and revision |
| `0061-0100` | Basic parser and safe renderer |
| `0101-0140` | Render cache and metadata extraction |
| `0141-0190` | User identity and ACL MVP |
| `0191-0240` | Discussion MVP |
| `0241-0290` | Search adapter and local fallback |
| `0291-0340` | Job queue abstraction and indexing jobs |
| `0341-0400` | Admin/audit basics |

The backlog must be replenished before `tasks/queue` becomes empty.

