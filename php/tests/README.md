# php/tests

PHP test suite.

- `Persistence/ConnectionConfigTest.php` (0484) — confirms
  `MintWiki\Persistence\ConnectionConfig` returns the `driver`, `host`,
  `port`, `database`, `username`, and `password` passed to its
  constructor. Run it with `php tests/Persistence/ConnectionConfigTest.php`
  from `php/` after `composer install`.
- `Persistence/PdoConnectionFactoryTest.php` (0484) — confirms
  `MintWiki\Persistence\PdoConnectionFactory::dsn()` builds the expected
  PDO DSN string for both the `pgsql` (PostgreSQL) and `mysql` (MariaDB)
  drivers, and rejects unsupported drivers with an
  `InvalidArgumentException`. It does not open a real `PDO` connection —
  actual connectivity is covered separately by
  `scripts/mariadb_smoke_check.py` / `scripts/postgresql_smoke_check.py`.
  Run it with `php tests/Persistence/PdoConnectionFactoryTest.php` from
  `php/` after `composer install`.
- `Persistence/PdoTransactionTest.php` (0485) — confirms
  `MintWiki\Persistence\PdoTransaction::begin()`/`commit()`/`rollback()`
  delegate to the underlying `PDO` connection's transaction methods, using
  an in-memory `pdo_sqlite` connection so the test stays network-free.
  Run it with `php tests/Persistence/PdoTransactionTest.php` from `php/`
  after `composer install`.

These tests run without phpunit, directly via the `php` CLI, and without
any network dependency (`composer.json` declares no packages beyond the
`php` engine constraint, so `composer install` itself needs no network
access either).
