# php/tests

PHP test suite.

- `AutoloadSmokeTest.php` (0393) — confirms `composer install` (no network
  calls; `composer.json` declares no packages beyond the `php` engine
  constraint) generates a `vendor/autoload.php` whose `MintWiki\` PSR-4
  prefix maps to `src/`. Run it directly with `php tests/AutoloadSmokeTest.php`
  from `php/` after `composer install`. It exits non-zero with a clear
  message if `vendor/` is missing, instead of crashing.
- `Http/ResponseTest.php` (0395) — confirms `MintWiki\Http\Response`
  returns the `status`, `headers`, and `body` passed to its constructor
  (and sensible defaults when omitted). Run it with
  `php tests/Http/ResponseTest.php` from `php/` after `composer install`.
- `Http/RequestTest.php` (0396) — confirms `MintWiki\Http\Request`
  returns the `method`, `path`, `query`, `body`, and `headers` passed to
  its constructor (and sensible defaults when omitted). Run it with
  `php tests/Http/RequestTest.php` from `php/` after `composer install`.
- `Http/RouterTest.php` (0397) — confirms `MintWiki\Http\Router` matches
  a registered route only when both method (case-insensitively) and path
  match exactly, and returns `null` otherwise (no dynamic segments or
  partial matches). Run it with `php tests/Http/RouterTest.php` from
  `php/` after `composer install`.

Fixture runners (0398, 0406, 0407, ...) are added by later Phase B tasks
and must likewise run without any network dependency
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

Cross-language fixtures these runners consume live under
`tests/modules/<module>/fixtures/` or `tests/fixtures/` in the repository
root (`docs/fixture-directory-convention.md`), not here.
