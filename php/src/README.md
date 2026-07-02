# php/src

PHP application and module source, namespaced under `MintWiki\`
(`docs/php-namespace-mapping.md`).

- `Persistence/` (0484, 0485, 0486) — `ConnectionConfig` and
  `PdoConnectionFactory`, the PDO connection skeleton shared by
  PostgreSQL and MariaDB. Follows the connection-ownership contract in
  `docs/db-adapter-contract.md` §1: this factory only builds and hands
  off a `PDO` instance, it does not own a session or get called from
  Repository/Service code directly. `PdoTransaction` (0485) wraps an
  injected `PDO` instance with the `begin`/`commit`/`rollback` contract
  from `docs/db-adapter-contract.md` §2 — nothing more. `SqlDialect` (0486)
  is an enum representing the supported SQL dialects (MySQL, PostgreSQL, SQLite).
- `Modules/Document/` (0487) — Document module's SQL repository skeleton.
  `Document` is the domain model, and `DocumentRepository` exposes the
  create/get/get_by_normalized_title/update contract from
  `docs/db-adapter-contract.md` §2. SQL implementation is placeholder for now.
