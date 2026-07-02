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
- `Http/RouteRegistrationTest.php` (0398) — confirms `Router::register()`
  registers multiple routes independently (using `home`/`health`
  placeholder routes as examples) and that re-registering the same
  method+path replaces the previous handler without affecting other
  routes. Run it with `php tests/Http/RouteRegistrationTest.php` from
  `php/` after `composer install`.
- `Modules/Document/DocumentTest.php` (0400, 0401) — confirms
  `MintWiki\Document\Document` returns the `id`, `title`, and
  `currentRevisionId` passed to its constructor (with `currentRevisionId`
  defaulting to `null`), that `normalizedTitle` is trimmed/collapsed via
  `Title::normalize()`, and that a whitespace-only title raises
  `EmptyTitleError`. Run it with
  `php tests/Modules/Document/DocumentTest.php` from `php/` after
  `composer install`.
- `Modules/Document/TitleTest.php` (0401) — confirms
  `MintWiki\Document\Title::normalize()` trims/collapses whitespace and
  rejects empty/whitespace-only titles with `EmptyTitleError`
  (`EmptyTitleError::CODE === 'document.empty_title'`), using the same
  scenarios as `tests/modules/document/fixtures/`. Run it with
  `php tests/Modules/Document/TitleTest.php` from `php/` after
  `composer install`.

- `Modules/Document/RepositoryTest.php` (0402) — confirms
  `MintWiki\Document\Repository` is an interface implementable with the
  `create`/`get`/`getByNormalizedTitle`/`update` contract from
  `docs/repository-port-contracts.md` (via an anonymous in-memory
  implementation), and that `DuplicateNormalizedTitleError::CODE` /
  `NotFoundError::CODE` expose `document.duplicate_title` /
  `document.not_found`. No concrete repository implementation ships in
  this task — that lands in 0435. Run it with
  `php tests/Modules/Document/RepositoryTest.php` from `php/` after
  `composer install`.
- `Modules/Document/ServiceTest.php` (0403) — confirms
  `MintWiki\Document\Service::create()`/`get()` (against an anonymous
  in-memory `Repository`) issue a non-empty, unique id per document,
  return the created document by id, return `null` for a missing id,
  and propagate `EmptyTitleError`/`DuplicateNormalizedTitleError` from
  `Document`/`Repository::create()`. Only the `create`/`get` contract
  from `docs/service-method-contracts.md` is covered — `get_by_title`
  and `get_current_revision_read_model` are out of scope until the
  revision port exists (0404/0405). Run it with
  `php tests/Modules/Document/ServiceTest.php` from `php/` after
  `composer install`.

- `Modules/Revision/RevisionTest.php` (0404) — confirms
  `MintWiki\Revision\Revision` returns the `id`, `documentId`, `source`,
  `authorId`, `summary`, and `parentRevisionId` passed to its constructor
  (with `parentRevisionId` defaulting to `null`), and that `source` is
  stored verbatim (no normalization, including multi-line values). Run
  it with `php tests/Modules/Revision/RevisionTest.php` from `php/`
  after `composer install`.

Fixture runners (0406, 0407, ...) are added by later Phase B tasks and
must likewise run without any network dependency
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

Cross-language fixtures these runners consume live under
`tests/modules/<module>/fixtures/` or `tests/fixtures/` in the repository
root (`docs/fixture-directory-convention.md`), not here.
