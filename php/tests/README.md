# php/tests

PHP test suite.

- `AutoloadSmokeTest.php` (0393) — confirms `composer install` (no network
  calls; `composer.json` declares no packages beyond the `php` engine
  constraint) generates a `vendor/autoload.php` whose `MintWiki\` PSR-4
  prefix maps to `src/`. Run it directly with `php tests/AutoloadSmokeTest.php`
  from `php/` after `composer install`. It exits non-zero with a clear
  message if `vendor/` is missing, instead of crashing.

Fixture runners (0398, 0406, 0407, ...) are added by later Phase B tasks
and must likewise run without any network dependency
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

Cross-language fixtures these runners consume live under
`tests/modules/<module>/fixtures/` or `tests/fixtures/` in the repository
root (`docs/fixture-directory-convention.md`), not here.
