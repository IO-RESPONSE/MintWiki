# php/src

PHP application and module source, namespaced under `MintWiki\`
(`docs/php-namespace-mapping.md`).

- `Persistence/` (0484) — `ConnectionConfig` and `PdoConnectionFactory`,
  the PDO connection skeleton shared by PostgreSQL and MariaDB. Follows
  the connection-ownership contract in `docs/db-adapter-contract.md` §1:
  this factory only builds and hands off a `PDO` instance, it does not
  own a session or get called from Repository/Service code directly.
