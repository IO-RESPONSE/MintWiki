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
- `Persistence/SqlDialectTest.php` (0486) — confirms
  `MintWiki\Persistence\SqlDialect` enum cases and methods (`tryFrom`,
  `tryFromDriver`, `fromDriver`) work correctly. Run it with
  `php tests/Persistence/SqlDialectTest.php` from `php/` after
  `composer install`.
- `Persistence/SeedLoaderTest.php` (0492) — confirms
  `MintWiki\Persistence\SeedLoader` parses and loads ANSI SQL seed
  fixtures from `tests/fixtures/seed/*.sql` files. Tests SQL parsing
  (INSERT statement extraction, comment removal) and fixture loading
  (individual table and all-seeds modes). Uses an in-memory `pdo_sqlite`
  connection so the test stays network-free. Seed fixture files support
  PostgreSQL and MariaDB transparently. Run it with
  `php tests/Persistence/SeedLoaderTest.php` from `php/` after
  `composer install`.
- `Persistence/InstallerDBCheckTest.php` (0519) — confirms
  `MintWiki\Installer\DBCheck` validates database connection, charset
  (utf8mb4 for MariaDB, UTF8 for PostgreSQL), and schema version presence.
  Uses an in-memory `pdo_sqlite` connection so the test stays network-free.
  Run it with `php tests/Persistence/InstallerDBCheckTest.php` from `php/`
  after `composer install`.
- `Modules/Document/DocumentRepositoryTest.php` (0487) — confirms
  `MintWiki\Modules\Document\DocumentRepository` skeleton and `Document`
  domain model are correctly structured. Uses an in-memory `pdo_sqlite`
  connection so the test stays network-free. SQL implementation is
  placeholder for now. Run it with
  `php tests/Modules/Document/DocumentRepositoryTest.php` from `php/`
  after `composer install`.

These tests run without phpunit, directly via the `php` CLI, and without
any network dependency (`composer.json` declares no packages beyond the
`php` engine constraint, so `composer install` itself needs no network
access either).
