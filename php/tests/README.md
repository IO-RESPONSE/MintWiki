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
- `Modules/Document/TitleFixtureRunnerTest.php` (0426) — reads every
  cross-language JSON fixture under the repository root's
  `tests/modules/document/fixtures/` via `Support/FixtureLoader.php`
  (0425) and runs it against `MintWiki\Document\Title::normalize()`,
  matching Python's `tests/modules/document/test_title_fixtures.py`:
  success fixtures compare the return value to `expected.title`,
  failure fixtures confirm `EmptyTitleError` is thrown and its `CODE`
  is in the fixture's `errors` list. Unlike `TitleTest.php`, this file
  reads the fixture files directly instead of hand-copying scenario
  values, so future fixture edits are picked up without touching PHP
  code. Run it with
  `php tests/Modules/Document/TitleFixtureRunnerTest.php` from `php/`
  after `composer install`.

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
- `Modules/Revision/RepositoryTest.php` (0405) — confirms
  `MintWiki\Revision\Repository` is an interface implementable with the
  `create`/`get`/`listByDocumentId` contract from
  `docs/repository-port-contracts.md` (via an anonymous in-memory
  implementation), and that `listByDocumentId` returns only the
  revisions for the given document in creation order. No `update`/
  `delete` methods exist — revisions are append-only. No concrete
  repository implementation ships in this task — that lands in 0435.
  Run it with `php tests/Modules/Revision/RepositoryTest.php` from
  `php/` after `composer install`.

- `Modules/Parser/FixtureRunner.php` / `Modules/Parser/FixtureRunnerTest.php`
  (0406) — `FixtureRunner` reads the cross-language JSON fixtures under
  `tests/modules/parser/fixtures/` (`docs/cross-language-fixture-schema.md`)
  directly with `json_decode` (the shared JSON fixture loader lands
  separately in 0425) and runs them against any `callable(string $source): array`
  parse callback, comparing the callback's return value to the fixture's
  `expected` field. The parser module's PHP port is still a placeholder
  (0399), so the test exercises `FixtureRunner` itself — listing/loading
  fixtures and detecting match/mismatch — against stub callbacks rather
  than a real parser. Run it with
  `php tests/Modules/Parser/FixtureRunnerTest.php` from `php/` after
  `composer install`.

- `Modules/Acl/DecisionTest.php` (0408) — confirms
  `MintWiki\Acl\Decision` returns the `permission`, `allowed`, `reason`,
  and `matchedRuleId` passed to its constructor (with `matchedRuleId`
  defaulting to `null`), and that `isAllowed()`/`isDenied()` mirror the
  `allowed` flag for both the matched-allow and matched-deny cases (a
  denied decision can still carry `reason === 'acl.matched_rule'` when a
  deny rule matched, versus `acl.no_matching_rule` when none did — see
  `tests/modules/acl/fixtures/`). No rule-evaluation logic (`AclService`)
  ships in this task. Run it with `php tests/Modules/Acl/DecisionTest.php`
  from `php/` after `composer install`.

- `Modules/Render/FixtureRunner.php` / `Modules/Render/FixtureRunnerTest.php`
  (0407) — `FixtureRunner` reads the cross-language JSON fixtures under
  `tests/modules/render/fixtures/` (`docs/cross-language-fixture-schema.md`)
  directly with `json_decode` and runs them against any
  `callable(array $input): mixed` render callback, comparing the
  callback's return value to the fixture's `expected` field. Unlike the
  parser runner, it passes the whole `input` array (not a single
  `source` string) to the callback, since render fixtures vary per
  function (`escape_html` takes `text`, `render_heading` takes `level`/
  `content`, etc.) — same reasoning as `tests/modules/render/fixtures/`
  mixing `.json` cross-language fixtures with pre-existing `.html`
  snapshot fixtures, which `listFixtures()` excludes via its `*.json`
  glob. The render module's PHP port is still a placeholder (0399), so
  the test exercises `FixtureRunner` itself against a stub callback
  rather than a real render function. Run it with
  `php tests/Modules/Render/FixtureRunnerTest.php` from `php/` after
  `composer install`.

- `Modules/User/UserTest.php` (0409) — confirms `MintWiki\User\User`
  returns the `id`, `username`, and `displayName` passed to its
  constructor (with `displayName` defaulting to `null`), preserves a
  unicode `username` verbatim, and throws `EmptyUsernameError` for an
  empty or whitespace-only `username`. Run it with
  `php tests/Modules/User/UserTest.php` from `php/` after
  `composer install`.
- `Modules/User/AnonymousIdentityTest.php` (0409) — confirms
  `MintWiki\User\AnonymousIdentity::isAnonymous()` returns `true` and
  that each instance is distinct (no shared/singleton state). Run it
  with `php tests/Modules/User/AnonymousIdentityTest.php` from `php/`
  after `composer install`.
- `Modules/User/IpIdentityTest.php` (0409) — confirms
  `MintWiki\User\IpIdentity` returns the IPv4/IPv6 `ipAddress` passed to
  its constructor, that `isAnonymous()` returns `true`, and that an
  invalid or empty address raises `InvalidIpAddressError`. Run it with
  `php tests/Modules/User/IpIdentityTest.php` from `php/` after
  `composer install`.

- `Modules/Discussion/ThreadTest.php` (0410) — confirms
  `MintWiki\Discussion\Thread` returns the `id`/`documentId`/`title`/
  `createdBy`/`createdAt`/`status`/`closedAt`/`pausedAt` passed to (or
  defaulted by) its constructor, that `title` is trimmed/collapsed like
  `Document\Title::normalize`, that `close()`/`reopen()`/`pause()` update
  `status` unconditionally and that `closedAt`/`pausedAt` are not
  mutually reset (`reopen()` only clears `closedAt`), and that a blank
  `id`/`documentId`/`title`/`createdBy` raises the matching
  `EmptyThread*Error`. Run it with
  `php tests/Modules/Discussion/ThreadTest.php` from `php/` after
  `composer install`.
- `Modules/Discussion/CommentTest.php` (0410) — confirms
  `MintWiki\Discussion\Comment` returns the `id`/`threadId`/`body`/
  `createdBy`/`createdAt`/`isHidden`/`hiddenAt` passed to (or defaulted
  by) its constructor, that `body` is stored verbatim (no
  trim/normalization), that `hide()` is idempotent and never clears
  `body`, that `toPublicView()` masks `body` to `null` only while hidden
  and `toModeratorView()` never does, and that a blank
  `id`/`threadId`/`body`/`createdBy` raises the matching
  `EmptyComment*Error`. Run it with
  `php tests/Modules/Discussion/CommentTest.php` from `php/` after
  `composer install`.
- `Modules/Discussion/ThreadStateTest.php` (0410) — confirms
  `MintWiki\Discussion\ThreadState` is a string-backed enum with
  `Open`/`Closed`/`Paused` cases whose values are `'open'`/`'closed'`/
  `'paused'`. Run it with
  `php tests/Modules/Discussion/ThreadStateTest.php` from `php/` after
  `composer install`.

- `Modules/Cache/BackendTest.php` (0411) — confirms
  `MintWiki\Cache\Backend` is an interface implementable with the
  `get`/`set`/`delete` contract (via an anonymous in-memory
  implementation), and that `get` returns `null` for a missing key,
  reflects the most recent `set` for a given key, and returns `null`
  again after `delete`. `clear()` and TTL/expiry are out of scope for
  this task. No concrete backend implementation ships in this task —
  that lands in a later task. Run it with
  `php tests/Modules/Cache/BackendTest.php` from `php/` after
  `composer install`.

- `Modules/Jobs/RunnerTest.php` (0412) — confirms `MintWiki\Jobs\Runner`
  is an interface implementable with the `enqueue`/`runSync`/`getStatus`
  contract (via an anonymous sync-fallback implementation), that
  `runSync()` executes a job directly without going through `enqueue()`,
  that `enqueue()` returns a non-empty, unique job id per call, and that
  `getStatus()` returns `null` for an unknown job id and otherwise
  returns the result `enqueue()` already produced synchronously (the
  shared hosting fallback: no worker needed). No concrete `Runner`
  implementation (sync or queued) ships in this task — that lands in a
  later task. Run it with `php tests/Modules/Jobs/RunnerTest.php` from
  `php/` after `composer install`.

- `Modules/Audit/AuditEventTest.php` (0413) — confirms
  `MintWiki\Audit\AuditEvent` returns the `id`/`module`/`action`/
  `occurredAt`/`actorId`/`metadata` passed to (or defaulted by) its
  constructor (`actorId` defaults to `null`, `metadata` defaults to
  `[]`), that all its properties are `readonly` (append-only: no
  mutator methods), and that a blank `id`/`module`/`action` raises the
  matching `EmptyAuditEvent*Error`. No service/repository port
  (`record`/`list_events`) ships in this task. Run it with
  `php tests/Modules/Audit/AuditEventTest.php` from `php/` after
  `composer install`.

- `Modules/Admin/ServiceTest.php` (0414) — confirms `MintWiki\Admin\Service`
  exposes the six placeholder methods (`blockUser`/`unblockUser`/
  `protectPage`/`unprotectPage`/`submitReport`/`resolveReport`) matching
  `src/modules/admin/manifest.json`'s `service.public_methods`, and that
  calling any of them throws `\LogicException` — the Python admin
  implementation does not exist yet (tasks 0345-0350 are still queued),
  so this task only reserves the method names. Run it with
  `php tests/Modules/Admin/ServiceTest.php` from `php/` after
  `composer install`.

- `Http/HealthRouteTest.php` (0419) — confirms the `GET /health` handler
  `public/index.php` registers on `MintWiki\Http\Router` returns a
  `200` JSON response (`Content-Type: application/json`) with
  `{"status": "ok", "app": "wiki-engine"}` by default, that a
  `WIKI_APP_NAME` environment variable overrides the `app` value (via
  `MintWiki\App\ConfigLoader`), and that other methods/paths
  (`POST /health`, `GET /other`) still don't match. The full
  over-HTTP behavior of `public/index.php` (including the
  placeholder-text fallback for non-`/health` requests) is covered by
  `tests/test_php_public_front_controller.py` (Python, `php -S`) in the
  repository root. Run it with `php tests/Http/HealthRouteTest.php` from
  `php/` after `composer install`.
- `Http/DocumentApiRoutesTest.php` (0420) — confirms
  `MintWiki\Http\DocumentApiRoutes::register()` registers the document API
  paths that don't need a dynamic segment (`GET`/`POST /api/documents`,
  `GET /api/documents/by-title`, matching `src/modules/document/router.py`'s
  `/api/documents` prefix) on a `Router`, and that each returns a `501`
  JSON response (`{"error": "not_implemented"}`) with no repository/service
  wired up yet. Dynamic-segment paths (`/api/documents/{id}`,
  `/api/documents/{id}/revisions`) are out of scope until `Router` supports
  dynamic segments. Run it with `php tests/Http/DocumentApiRoutesTest.php`
  from `php/` after `composer install`.
- `App/ConfigLoaderTest.php` (0415) — confirms `MintWiki\App\ConfigLoader::get()`
  prefers a `WIKI_`-prefixed environment variable when set, falls back to
  the constructor-provided file-value array when the environment variable
  is absent, and returns the caller's `$default` (or `null`) when neither
  is present. No `.env`/config file parser ships in this task — that
  lands in 0616. Run it with `php tests/App/ConfigLoaderTest.php` from
  `php/` after `composer install`.

- `Support/FixtureLoader.php` / `Support/FixtureLoaderTest.php` (0425) —
  `FixtureLoader` reads the cross-language JSON fixtures under the
  repository root's `tests/modules/<module>/fixtures/` and
  `tests/fixtures/` (`docs/fixture-directory-convention.md`) with
  `json_decode`, providing `moduleFixtureDir()`/`sharedFixtureDir()`/
  `listFixtures()`/`loadFixture()` for reuse by future module parity
  tests (`docs/php-parity-test-plan.md`'s 0426+ plan). It does not
  replace `Modules/Parser/FixtureRunner.php` or `Modules/Render/
  FixtureRunner.php`, which predate this task and keep their own
  loading logic. Run it with `php tests/Support/FixtureLoaderTest.php`
  from `php/` after `composer install`.

Further fixture runners (...) are added by later Phase B tasks and must
likewise run without any network dependency
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

Cross-language fixtures these runners consume live under
`tests/modules/<module>/fixtures/` or `tests/fixtures/` in the repository
root (`docs/fixture-directory-convention.md`), not here.
