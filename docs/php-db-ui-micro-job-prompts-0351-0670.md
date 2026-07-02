# PHP, ANSI DB, UI micro job prompts 0351-0670

이 문서는 0350 완료 이후 큐에 **추가만** 할 마이크로 잡 프롬프트 원본이다.
기존 `tasks/` 파일은 수정, 이동, 삭제하지 않는다. 실제 큐 투입 시에는 이 문서의
항목을 `tasks/queue/0351-...md` 형식으로 새 파일 추가만 한다.

## Queue policy

- 0351 이후 순서는 `PHP 전환 기반 -> ANSI/MariaDB DB 모듈 -> 화면단 -> 웹호스팅 배포`로 고정한다.
- Python 구현은 당장 폐기하지 않고, PHP와 1:1로 교체 가능한 계약을 먼저 고정한다.
- DB는 PostgreSQL 전용 기능을 기본 경로에서 금지하고 ANSI SQL + MariaDB 호환성을 우선한다.
- UI는 PHP 전환과 DB 이식성 경계가 잡힌 뒤 서버 렌더링 중심으로 시작한다.
- 각 잡은 기존 템플릿의 Goal, Scope, Acceptance Criteria, Out of Scope, QA, Notes 구조를 사용한다.

## Common acceptance criteria

각 잡에는 아래 공통 기준을 넣는다.

- The task implements only the behavior named in the goal.
- Relevant tests or fixtures are added or updated.
- Existing tests continue to pass.
- The change is small enough to review as one runner cycle.
- Work from later task numbers is out of scope.
- Broad refactors across unrelated modules are out of scope.

## Common QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Phase A: PHP Replacement Contract, 0351-0390

목표: Python 모듈을 PHP 모듈로 1:1 교체하기 위한 언어 독립 계약을 고정한다.

| ID | Task title | Goal | Scope | Notes |
|---|---|---|---|---|
| 0351 | Document PHP replacement strategy | PHP 전환 전략과 1:1 모듈 교체 원칙을 문서화한다. | docs | Python 유지 기간, PHP 전환 기준, 금지할 결합을 명시한다. |
| 0352 | Add portability terminology glossary | 포팅 관련 용어집을 추가한다. | docs | port, adapter, contract, fixture, shared hosting 의미를 고정한다. |
| 0353 | Add module contract manifest schema | 모듈 계약 manifest 스키마를 추가한다. | docs, src/modules | 각 모듈의 port, service, repository, fixture 위치를 선언한다. |
| 0354 | Add document module contract manifest | document 모듈 계약 manifest를 추가한다. | src/modules/document | PHP 대응 네임스페이스 후보를 포함한다. |
| 0355 | Add revision module contract manifest | revision 모듈 계약 manifest를 추가한다. | src/modules/revision | 리비전 생성/조회 계약을 언어 독립적으로 적는다. |
| 0356 | Add parser module contract manifest | parser 모듈 계약 manifest를 추가한다. | src/modules/parser | 입력 source와 AST/토큰 출력 계약을 고정한다. |
| 0357 | Add render module contract manifest | render 모듈 계약 manifest를 추가한다. | src/modules/render | XSS 이스케이프 책임 경계를 명시한다. |
| 0358 | Add user module contract manifest | user 모듈 계약 manifest를 추가한다. | src/modules/user | 세션, 그룹, 차단 계약을 분리한다. |
| 0359 | Add ACL module contract manifest | ACL 모듈 계약 manifest를 추가한다. | src/modules/acl | 권한 결정 입력/출력 모델을 고정한다. |
| 0360 | Add discussion module contract manifest | discussion 모듈 계약 manifest를 추가한다. | src/modules/discussion | thread/comment/state 계약을 고정한다. |
| 0361 | Add cache module contract manifest | cache 모듈 계약 manifest를 추가한다. | src/modules/cache | PHP에서 선택 구현 가능한 cache port를 명시한다. |
| 0362 | Add jobs module contract manifest | jobs 모듈 계약 manifest를 추가한다. | src/modules/jobs | shared hosting에서는 sync fallback이 기본임을 명시한다. |
| 0363 | Add audit module contract manifest | audit 모듈 계약 manifest를 추가한다. | src/modules/audit | append-only 계약과 실패 정책을 고정한다. |
| 0364 | Add admin module contract manifest | admin 모듈 계약 manifest를 추가한다. | src/modules/admin | 관리자 액션은 audit hook을 통과해야 함을 명시한다. |
| 0365 | Add contract manifest validation script | manifest 필수 필드를 검증하는 스크립트를 추가한다. | scripts, tests | 누락된 모듈 계약을 QA에서 잡는다. |
| 0366 | Add manifest validation to QA | QA에 manifest 검증을 연결한다. | scripts/qa.sh, tests | 기존 boundary check와 함께 실행한다. |
| 0367 | Document Python to PHP namespace mapping | Python 패키지와 PHP namespace 매핑을 문서화한다. | docs | `modules.document.service`와 `MintWiki\Document\Service` 식으로 고정한다. |
| 0368 | Add shared fixture directory convention | 교차언어 fixture 디렉터리 규칙을 추가한다. | docs, tests/fixtures | JSON fixture를 기본으로 한다. |
| 0369 | Add cross-language fixture schema | Python/PHP 공용 fixture JSON 스키마를 추가한다. | docs, tests/fixtures | input, expected, errors 구조를 고정한다. |
| 0370 | Convert document title tests to shared fixtures | 문서 제목 정규화 테스트를 공용 fixture 기반으로 보강한다. | tests/modules/document | PHP가 같은 fixture를 재사용할 수 있게 한다. |
| 0371 | Convert parser tests to shared fixtures | parser 테스트 일부를 공용 fixture 기반으로 보강한다. | tests/modules/parser | 정규식 차이를 조기에 잡는다. |
| 0372 | Convert render tests to shared fixtures | render 테스트 일부를 공용 fixture 기반으로 보강한다. | tests/modules/render | HTML output fixture를 안정화한다. |
| 0373 | Add portable exception code policy | 예외 메시지 대신 안정적인 error code 정책을 문서화한다. | docs | PHP와 Python이 같은 code를 반환하게 한다. |
| 0374 | Add document error codes | document 모듈 error code 상수를 추가한다. | src/modules/document, tests | duplicate, not_found, empty_title 등을 고정한다. |
| 0375 | Add ACL decision code fixtures | ACL decision 결과 코드를 fixture로 고정한다. | src/modules/acl, tests | allow/deny/reason code를 언어 독립화한다. |
| 0376 | Add DTO naming convention docs | Python schema와 PHP DTO 네이밍 규칙을 문서화한다. | docs | Request/Response/ReadModel 구분을 고정한다. |
| 0377 | Add service method contract docs | 서비스 메서드 입출력 계약 문서를 추가한다. | docs | 모듈별 public method만 적는다. |
| 0378 | Add repository port contract docs | 저장소 포트 계약 문서를 추가한다. | docs | ORM 의존 없는 인터페이스 기준으로 적는다. |
| 0379 | Add no-framework-domain boundary test | 도메인 계층 프레임워크 import 금지 검사를 보강한다. | scripts, tests | PHP 전환 가능성을 해치는 import를 차단한다. |
| 0380 | Add no-app-import-in-modules check | 모듈 도메인이 app 계층을 import하지 못하게 검사한다. | scripts, tests | UI/API 어댑터 역참조를 차단한다. |
| 0381 | Add pure Python value object checklist | PHP 전환 대상 value object 체크리스트를 추가한다. | docs | dataclass/default/typing 사용 제한을 명시한다. |
| 0382 | Add portable datetime policy | datetime 저장/표시 정책을 문서화한다. | docs | UTC 저장, 표시 timezone 분리를 명시한다. |
| 0383 | Add portable ID policy | ID 생성과 저장 정책을 문서화한다. | docs | DB native UUID 대신 문자열 ID 기본을 고정한다. |
| 0384 | Add portable pagination contract | pagination 계약을 문서화한다. | docs, tests | limit/offset 기본, cursor는 adapter 뒤로 둔다. |
| 0385 | Add portable sorting contract | 정렬 계약을 문서화한다. | docs | DB별 NULL 정렬 차이를 피한다. |
| 0386 | Add portable text normalization policy | 텍스트 정규화 정책을 문서화한다. | docs | Unicode normalization과 case 정책을 명시한다. |
| 0387 | Add PHP parity test plan | PHP parity 테스트 계획을 문서화한다. | docs | 같은 fixture를 양쪽 런타임에서 실행하는 방식을 적는다. |
| 0388 | Add PHP replacement readiness checklist | PHP 전환 준비 체크리스트를 추가한다. | docs | 모듈별 ready/not-ready 기준을 둔다. |
| 0389 | Add contract drift report placeholder | Python/PHP 계약 drift 리포트 placeholder를 추가한다. | docs, scripts | 초기에는 문서/스크립트 골격만 둔다. |
| 0390 | Add portability phase QA checklist | Phase A 완료 QA 체크리스트를 추가한다. | docs | manifest, fixtures, boundary, docs 검증을 포함한다. |

## Phase B: PHP Runtime Skeleton, 0391-0440

목표: Python 모듈을 대체할 PHP 런타임 골격을 추가하되, 아직 전체 기능 포팅은 하지 않는다.

| ID | Task title | Goal | Scope | Notes |
|---|---|---|---|---|
| 0391 | Add PHP runtime directory skeleton | PHP 런타임 기본 디렉터리를 추가한다. | php | `php/src`, `php/public`, `php/tests` 골격만 추가한다. |
| 0392 | Add PHP composer manifest | Composer manifest를 추가한다. | php/composer.json | shared hosting 대응을 위해 의존성은 최소화한다. |
| 0393 | Add PHP autoload smoke test | PHP autoload smoke test를 추가한다. | php/tests | 네트워크 의존 없이 동작하게 한다. |
| 0394 | Add PHP public front controller | `public/index.php` 골격을 추가한다. | php/public | 요청 정보를 읽고 placeholder 응답만 반환한다. |
| 0395 | Add PHP response abstraction | PHP Response value object를 추가한다. | php/src/Http | status, headers, body만 둔다. |
| 0396 | Add PHP request abstraction | PHP Request value object를 추가한다. | php/src/Http | method, path, query, body, headers를 둔다. |
| 0397 | Add PHP router skeleton | PHP router skeleton을 추가한다. | php/src/Http | 정적 route 매칭만 지원한다. |
| 0398 | Add PHP route registration test | PHP route 등록 테스트를 추가한다. | php/tests | home/health placeholder를 확인한다. |
| 0399 | Add PHP module namespace skeleton | PHP 모듈 namespace 골격을 추가한다. | php/src/Modules | Document, Revision, Parser 등 빈 namespace를 둔다. |
| 0400 | Add PHP document value object | PHP Document value object를 추가한다. | php/src/Modules/Document | Python Document 계약과 필드를 맞춘다. |
| 0401 | Add PHP document title normalizer | PHP 제목 정규화기를 추가한다. | php/src/Modules/Document, php/tests | shared fixture로 Python과 결과를 맞춘다. |
| 0402 | Add PHP document repository port | PHP DocumentRepository interface를 추가한다. | php/src/Modules/Document | 구현 없이 port만 둔다. |
| 0403 | Add PHP document service skeleton | PHP DocumentService skeleton을 추가한다. | php/src/Modules/Document | create/get 계약만 추가한다. |
| 0404 | Add PHP revision value object | PHP Revision value object를 추가한다. | php/src/Modules/Revision | Python Revision 필드와 맞춘다. |
| 0405 | Add PHP revision repository port | PHP RevisionRepository interface를 추가한다. | php/src/Modules/Revision | listByDocumentId 계약을 포함한다. |
| 0406 | Add PHP parser fixture runner | PHP parser fixture runner를 추가한다. | php/tests | 아직 parser 구현은 placeholder로 둔다. |
| 0407 | Add PHP render fixture runner | PHP render fixture runner를 추가한다. | php/tests | shared HTML fixture 실행 기반을 둔다. |
| 0408 | Add PHP ACL decision value object | PHP ACL Decision value object를 추가한다. | php/src/Modules/Acl | allow/reason/action/resource 계약을 맞춘다. |
| 0409 | Add PHP user identity value objects | PHP 사용자 identity value object를 추가한다. | php/src/Modules/User | anonymous/user/ip identity 구분을 둔다. |
| 0410 | Add PHP discussion value objects | PHP 토론 value object 골격을 추가한다. | php/src/Modules/Discussion | Thread/Comment/State를 둔다. |
| 0411 | Add PHP cache port | PHP cache port interface를 추가한다. | php/src/Modules/Cache | get/set/delete 기본만 둔다. |
| 0412 | Add PHP job port | PHP job port interface를 추가한다. | php/src/Modules/Jobs | shared hosting sync fallback을 고려한다. |
| 0413 | Add PHP audit event value object | PHP audit event value object를 추가한다. | php/src/Modules/Audit | append-only metadata를 둔다. |
| 0414 | Add PHP admin service skeleton | PHP admin service skeleton을 추가한다. | php/src/Modules/Admin | block/protect/report placeholder만 둔다. |
| 0415 | Add PHP config loader | PHP config loader skeleton을 추가한다. | php/src/App | env/config file에서 읽는 계약만 둔다. |
| 0416 | Add PHP error code registry | PHP error code registry를 추가한다. | php/src/App, php/tests | Python error code와 이름을 맞춘다. |
| 0417 | Add PHP JSON response helper | PHP JSON 응답 helper를 추가한다. | php/src/Http | API compatibility를 위한 기반이다. |
| 0418 | Add PHP HTML response helper | PHP HTML 응답 helper를 추가한다. | php/src/Http | UI 단계 전 서버 렌더링 기반만 둔다. |
| 0419 | Add PHP health endpoint | PHP `/health` endpoint를 추가한다. | php/public, php/src | 앱 이름과 status를 반환한다. |
| 0420 | Add PHP document API placeholder routes | PHP document API placeholder route를 추가한다. | php/src/Http | 아직 저장소 연결 없이 501 계약을 둔다. |
| 0421 | Add PHP test bootstrap docs | PHP 테스트 실행 문서를 추가한다. | docs, php | composer/phpunit 선택 기준을 적는다. |
| 0422 | Add PHP coding standard docs | PHP 코딩 표준을 문서화한다. | docs | PSR-4, strict_types, namespace 규칙을 둔다. |
| 0423 | Add PHP static analysis plan | PHP static analysis 계획을 문서화한다. | docs | PHPStan/Psalm 도입은 후속 잡으로 둔다. |
| 0424 | Add PHP no-framework-domain rule | PHP 도메인 계층 framework 금지 규칙을 문서화한다. | docs | Python boundary와 같은 원칙이다. |
| 0425 | Add PHP shared fixture loader | PHP shared fixture loader를 추가한다. | php/tests | JSON fixture를 읽는다. |
| 0426 | Add PHP document fixture parity tests | PHP document fixture parity test를 추가한다. | php/tests | title normalization부터 시작한다. |
| 0427 | Add PHP ACL fixture parity tests | PHP ACL fixture parity test를 추가한다. | php/tests | decision code fixture를 검증한다. |
| 0428 | Add PHP parser parity placeholders | PHP parser parity placeholder tests를 추가한다. | php/tests | 구현 전 expected failure 정책을 문서화한다. |
| 0429 | Add PHP render parity placeholders | PHP render parity placeholder tests를 추가한다. | php/tests | 구현 전 skipped test로 둔다. |
| 0430 | Add PHP runtime QA command script | PHP QA 스크립트 골격을 추가한다. | php/scripts | test/static check 명령을 한 곳에 둔다. |
| 0431 | Add root QA hook for optional PHP | 루트 QA에서 PHP QA를 선택 실행할 수 있게 한다. | scripts/qa.sh | PHP 도구가 없으면 명확히 skip한다. |
| 0432 | Add PHP runtime Docker note | PHP 런타임 로컬 테스트 note를 추가한다. | docs | shared hosting과 Docker를 구분한다. |
| 0433 | Add PHP module replacement matrix | 모듈별 Python/PHP 구현 상태 matrix를 추가한다. | docs | not-started/partial/parity/pass 상태를 둔다. |
| 0434 | Add PHP document service parity test | PHP DocumentService parity test를 추가한다. | php/tests | in-memory repository로 create/get을 검증한다. |
| 0435 | Add PHP in-memory document repository | PHP in-memory document repository를 추가한다. | php/src/Modules/Document | DB 전 단계 테스트용이다. |
| 0436 | Add PHP in-memory revision repository | PHP in-memory revision repository를 추가한다. | php/src/Modules/Revision | 문서/리비전 통합 테스트용이다. |
| 0437 | Add PHP document revision integration test | PHP 문서+리비전 통합 테스트를 추가한다. | php/tests | source가 첫 리비전으로 연결되는지 검증한다. |
| 0438 | Add PHP runtime security baseline docs | PHP 런타임 보안 기준을 문서화한다. | docs | escaping, session, upload, path traversal 기준을 둔다. |
| 0439 | Add PHP runtime phase QA checklist | PHP 런타임 phase QA 체크리스트를 추가한다. | docs | parity, autoload, health, module skeleton을 점검한다. |
| 0440 | Add PHP replacement readiness gate | PHP 전환 gate 문서를 추가한다. | docs | DB 단계로 넘어가기 전 완료 조건을 명시한다. |

## Phase C: ANSI SQL and MariaDB Portable DB Layer, 0441-0520

목표: DB 계층을 ANSI SQL 중심으로 재설계하고 PostgreSQL/MariaDB 양쪽에서 사용 가능하게 한다.

| ID | Task title | Goal | Scope | Notes |
|---|---|---|---|---|
| 0441 | Document ANSI SQL persistence policy | ANSI SQL persistence 정책을 문서화한다. | docs | PostgreSQL 전용 기능 금지 목록을 포함한다. |
| 0442 | Add MariaDB compatibility matrix | MariaDB 호환성 matrix를 추가한다. | docs | type, index, transaction, collation 차이를 적는다. |
| 0443 | Add portable schema naming policy | portable schema naming 정책을 추가한다. | docs | table/column/index 이름 길이와 예약어 회피를 다룬다. |
| 0444 | Add portable ID column policy | ID 컬럼 정책을 문서화한다. | docs | varchar/string UUID 기본을 둔다. |
| 0445 | Add portable timestamp column policy | timestamp 컬럼 정책을 문서화한다. | docs | UTC 저장, DB default 의존 최소화를 둔다. |
| 0446 | Add portable text collation policy | text collation 정책을 문서화한다. | docs | MariaDB collation 선택과 case sensitivity를 다룬다. |
| 0447 | Add SQL feature denylist check | 금지 SQL feature 검사 스크립트를 추가한다. | scripts, tests | RETURNING, ILIKE, JSONB 등 탐지한다. |
| 0448 | Add migration portability checklist | migration portability 체크리스트를 추가한다. | docs | Alembic/PHP migration 양쪽 기준을 둔다. |
| 0449 | Add DB adapter contract docs | DB adapter 계약 문서를 추가한다. | docs | Python/PHP 공통 repository가 의존할 최소 기능을 둔다. |
| 0450 | Add SQL dialect abstraction skeleton | SQL dialect abstraction skeleton을 추가한다. | src/persistence | placeholder만 두고 ORM 확장은 하지 않는다. |
| 0451 | Add portable query builder policy | query builder 사용 정책을 문서화한다. | docs | ad hoc string SQL 금지 기준을 둔다. |
| 0452 | Add document portable repository tests | document 저장소 portability 테스트를 추가한다. | tests/modules/document | SQLite/MariaDB 유사 제약을 우선 검증한다. |
| 0453 | Add revision portable repository tests | revision 저장소 portability 테스트를 추가한다. | tests/modules/revision | ordering과 FK를 검증한다. |
| 0454 | Add user portable repository plan | user 저장소 portability 계획을 추가한다. | docs | 세션/차단/그룹 테이블을 다룬다. |
| 0455 | Add ACL portable repository plan | ACL 저장소 portability 계획을 추가한다. | docs | rule precedence와 index 요구를 다룬다. |
| 0456 | Add discussion portable repository plan | discussion 저장소 portability 계획을 추가한다. | docs | comment pagination과 state를 다룬다. |
| 0457 | Add audit portable repository plan | audit 저장소 portability 계획을 추가한다. | docs | append-only, partition 없는 기본 설계를 둔다. |
| 0458 | Add jobs portable repository plan | jobs 저장소 portability 계획을 추가한다. | docs | shared hosting sync runner를 고려한다. |
| 0459 | Add portable migration directory skeleton | portable migration 디렉터리 골격을 추가한다. | db | Python/PHP 양쪽이 참고할 SQL 원본 위치다. |
| 0460 | Add base schema SQL draft | base schema SQL draft를 추가한다. | db/schema | ANSI 중심 create table 초안만 둔다. |
| 0461 | Add document table portable SQL | document table portable SQL을 추가한다. | db/schema | PostgreSQL/MariaDB 차이를 주석으로 분리한다. |
| 0462 | Add revision table portable SQL | revision table portable SQL을 추가한다. | db/schema | FK/index 이름을 portable하게 둔다. |
| 0463 | Add user table portable SQL | user table portable SQL 초안을 추가한다. | db/schema | password/session은 별도 테이블로 분리한다. |
| 0464 | Add session table portable SQL | session table portable SQL 초안을 추가한다. | db/schema | shared hosting 파일 세션 대안은 별도다. |
| 0465 | Add ACL table portable SQL | ACL table portable SQL 초안을 추가한다. | db/schema | namespace/document rule 구분을 둔다. |
| 0466 | Add discussion table portable SQL | discussion table portable SQL 초안을 추가한다. | db/schema | thread/comment/state를 둔다. |
| 0467 | Add audit table portable SQL | audit table portable SQL 초안을 추가한다. | db/schema | append-only event table을 둔다. |
| 0468 | Add jobs table portable SQL | jobs table portable SQL 초안을 추가한다. | db/schema | sync/queued 상태를 둔다. |
| 0469 | Add schema SQL lint test | schema SQL lint 테스트를 추가한다. | tests | 금지 타입/문법을 탐지한다. |
| 0470 | Add MariaDB DSN config placeholder | MariaDB DSN 설정 placeholder를 추가한다. | src/app, docs | 아직 드라이버 전환은 하지 않는다. |
| 0471 | Add PostgreSQL DSN compatibility docs | PostgreSQL DSN 호환 문서를 추가한다. | docs | 기존 개발 환경과 새 DB 정책을 연결한다. |
| 0472 | Add DB driver capability model | DB driver capability model을 추가한다. | src/persistence, tests | returning/json/fulltext 지원 여부를 표현한다. |
| 0473 | Add repository transaction policy | repository transaction 정책을 문서화한다. | docs | Python/PHP 양쪽 commit 경계를 맞춘다. |
| 0474 | Add portable duplicate key handling docs | duplicate key 처리 정책을 문서화한다. | docs | DB별 오류 메시지 의존을 금지한다. |
| 0475 | Add document duplicate handling test | document duplicate 처리 테스트를 보강한다. | tests/modules/document | error code 중심으로 검증한다. |
| 0476 | Add portable FK behavior tests | FK 동작 portability 테스트를 추가한다. | tests | cascade/restrict 정책을 고정한다. |
| 0477 | Add portable pagination SQL tests | pagination SQL portability 테스트를 추가한다. | tests | limit/offset 기반을 검증한다. |
| 0478 | Add portable sorting SQL tests | sorting SQL portability 테스트를 추가한다. | tests | NULL/locale 의존을 피한다. |
| 0479 | Add portable search DB boundary docs | DB search 경계 문서를 추가한다. | docs | fulltext는 adapter 뒤로 둔다. |
| 0480 | Add MariaDB migration smoke plan | MariaDB migration smoke 계획을 추가한다. | docs | 실제 CI 연결은 후속 잡이다. |
| 0481 | Add optional MariaDB test script | 선택 실행 MariaDB 테스트 스크립트를 추가한다. | scripts | DB가 없으면 skip한다. |
| 0482 | Add optional PostgreSQL test script | 선택 실행 PostgreSQL 테스트 스크립트를 추가한다. | scripts | 기존 환경과 병행한다. |
| 0483 | Add DB portability QA docs | DB portability QA 문서를 추가한다. | docs | 로컬/CI/수동 확인 경로를 둔다. |
| 0484 | Add PHP PDO connection skeleton | PHP PDO connection skeleton을 추가한다. | php/src/Persistence | MariaDB/PostgreSQL DSN을 모두 표현한다. |
| 0485 | Add PHP PDO transaction wrapper | PHP PDO transaction wrapper를 추가한다. | php/src/Persistence | begin/commit/rollback 계약만 둔다. |
| 0486 | Add PHP SQL dialect enum | PHP SQL dialect enum/value object를 추가한다. | php/src/Persistence | mysql/pgsql/sqlite 구분을 둔다. |
| 0487 | Add PHP document SQL repository skeleton | PHP document SQL repository skeleton을 추가한다. | php/src/Modules/Document | SQL은 아직 최소 placeholder다. |
| 0488 | Add PHP revision SQL repository skeleton | PHP revision SQL repository skeleton을 추가한다. | php/src/Modules/Revision | list ordering 계약을 둔다. |
| 0489 | Add PHP DB config docs | PHP DB 설정 문서를 추가한다. | docs, php | 웹호스팅 환경변수 부재 대안을 포함한다. |
| 0490 | Add DB portable seed fixtures | portable seed fixture를 추가한다. | tests/fixtures, db | 문서/리비전 기본 데이터를 둔다. |
| 0491 | Add Python seed loader for portable fixtures | Python seed loader를 추가한다. | tests, src/persistence | DB별 테스트 준비를 단순화한다. |
| 0492 | Add PHP seed loader for portable fixtures | PHP seed loader를 추가한다. | php/tests | parity 테스트 준비를 단순화한다. |
| 0493 | Add schema version table SQL | schema version table SQL을 추가한다. | db/schema | PHP 웹호스팅 installer가 사용할 수 있게 한다. |
| 0494 | Add migration state service skeleton | migration state service skeleton을 추가한다. | src/persistence, tests | DB 독립 상태 조회만 둔다. |
| 0495 | Add PHP migration state service skeleton | PHP migration state service skeleton을 추가한다. | php/src/Persistence | schema version table을 읽는다. |
| 0496 | Add portable backup format docs | portable backup format 문서를 추가한다. | docs | SQL dump와 JSON export 경계를 둔다. |
| 0497 | Add portable restore plan | portable restore 계획을 추가한다. | docs | MariaDB/PostgreSQL 차이를 다룬다. |
| 0498 | Add DB module boundary check | DB 모듈 경계 검사를 추가한다. | scripts, tests | 도메인이 SQLAlchemy/PDO를 직접 보지 않게 한다. |
| 0499 | Add DB phase risk register | DB phase risk register를 추가한다. | docs | collation, transaction, migration risk를 둔다. |
| 0500 | Add DB phase QA checklist | DB phase QA 체크리스트를 추가한다. | docs | ANSI lint, MariaDB smoke, PHP PDO skeleton을 포함한다. |
| 0501 | Add MariaDB local compose override docs | MariaDB 로컬 compose override 문서를 추가한다. | docs | 실제 compose 변경은 별도다. |
| 0502 | Add MariaDB compose profile | MariaDB compose profile을 추가한다. | docker-compose.yml | 기존 PostgreSQL profile과 충돌하지 않게 한다. |
| 0503 | Add MariaDB health check docs | MariaDB health check 문서를 추가한다. | docs | 운영자가 연결 상태를 확인할 방법을 둔다. |
| 0504 | Add DB config validation tests | DB 설정 검증 테스트를 추가한다. | tests | 지원 dialect와 DSN 오류를 검증한다. |
| 0505 | Add portable migration dry-run command | migration dry-run 명령 골격을 추가한다. | scripts | 실제 적용 없이 SQL 확인만 한다. |
| 0506 | Add DB schema compatibility report | schema compatibility report placeholder를 추가한다. | scripts, docs | PostgreSQL/MariaDB 차이 보고서 기반이다. |
| 0507 | Add DB adapter selection docs | DB adapter 선택 문서를 추가한다. | docs | Python, PHP, shared hosting 기준을 나눈다. |
| 0508 | Add DB module replacement matrix | DB 모듈 replacement matrix를 추가한다. | docs | Python repository/PHP PDO 상태를 추적한다. |
| 0509 | Add DB web hosting constraints docs | 웹호스팅 DB 제약 문서를 추가한다. | docs | 권한 제한, charset, migration 권한을 다룬다. |
| 0510 | Add DB phase readiness gate | DB 단계 완료 gate를 추가한다. | docs | UI 시작 전 필수 DB 조건을 명시한다. |
| 0511 | Add MariaDB collation fixture tests | MariaDB collation fixture 테스트 계획/placeholder를 추가한다. | tests, docs | 한글 제목 정렬/중복을 다룬다. |
| 0512 | Add portable LIKE search policy | portable LIKE 검색 정책을 추가한다. | docs | ILIKE 금지와 lower-normalized column 대안을 둔다. |
| 0513 | Add document lookup portable query tests | document lookup portable query 테스트를 추가한다. | tests/modules/document | normalized_title 조회를 검증한다. |
| 0514 | Add revision ordering portable tests | revision ordering portable 테스트를 추가한다. | tests/modules/revision | created_at/id tie-breaker 정책을 둔다. |
| 0515 | Add audit append portable tests | audit append portability 테스트를 추가한다. | tests/modules/audit | insert-only 경계를 둔다. |
| 0516 | Add jobs polling portable policy | jobs polling portability 정책을 추가한다. | docs | SKIP LOCKED 같은 전용 기능을 기본에서 제외한다. |
| 0517 | Add shared hosting migration policy | shared hosting migration 정책을 추가한다. | docs | 웹에서 실행 가능한 단계별 migration 기준을 둔다. |
| 0518 | Add PHP installer DB check skeleton | PHP installer DB check skeleton을 추가한다. | php/src/Installer | 접속/charset/schema version 확인만 둔다. |
| 0519 | Add installer DB check tests | installer DB check 테스트를 추가한다. | php/tests | mock PDO 또는 fake connection을 사용한다. |
| 0520 | Add ANSI DB phase summary | ANSI DB phase summary를 추가한다. | docs | 다음 UI 단계에서 지켜야 할 DB 경계를 요약한다. |

## Phase D: Server-rendered UI after PHP and DB, 0521-0610

목표: PHP/DB 전환 경계 위에서 웹호스팅 친화적인 서버 렌더링 화면을 만든다.

| ID | Task title | Goal | Scope | Notes |
|---|---|---|---|---|
| 0521 | Add UI architecture after PHP docs | PHP/DB 이후 UI 아키텍처를 문서화한다. | docs | 서버 렌더링, 정적 CSS/JS, no-build 기본을 둔다. |
| 0522 | Add PHP UI template skeleton | PHP UI template skeleton을 추가한다. | php/src/Ui | layout, escape helper만 둔다. |
| 0523 | Add PHP HTML escaping tests | PHP HTML escaping 테스트를 추가한다. | php/tests | XSS fixture를 사용한다. |
| 0524 | Add PHP static asset serving docs | PHP 정적 자산 제공 문서를 추가한다. | docs, php/public | shared hosting public 구조를 기준으로 한다. |
| 0525 | Add PHP base layout renderer | PHP base layout renderer를 추가한다. | php/src/Ui | header/main/footer landmark를 둔다. |
| 0526 | Add PHP home page route | PHP home page route를 추가한다. | php/src, php/public | 문서 검색 진입점만 둔다. |
| 0527 | Add UI design token CSS | UI design token CSS를 추가한다. | php/public/static | contrast, spacing, focus token을 둔다. |
| 0528 | Add UI accessibility baseline tests | UI 접근성 baseline 테스트를 추가한다. | php/tests | lang, viewport, labels, landmarks를 확인한다. |
| 0529 | Add PHP document view page | PHP document view page를 추가한다. | php/src/Ui, php/src/Modules/Document | 없는 문서 상태를 표시한다. |
| 0530 | Add PHP document create page | PHP document create page를 추가한다. | php/src/Ui | title/source 폼을 둔다. |
| 0531 | Add PHP document create handler | PHP document create handler를 추가한다. | php/src | DocumentService를 호출한다. |
| 0532 | Add PHP document edit page | PHP document edit page를 추가한다. | php/src/Ui | source textarea를 둔다. |
| 0533 | Add PHP document edit handler | PHP document edit handler를 추가한다. | php/src | 새 리비전을 생성한다. |
| 0534 | Add PHP document history page | PHP document history page를 추가한다. | php/src/Ui | 리비전 목록을 표시한다. |
| 0535 | Add PHP document diff placeholder | PHP diff placeholder page를 추가한다. | php/src/Ui | 실제 diff는 후속 작업이다. |
| 0536 | Add PHP search page shell | PHP search page shell을 추가한다. | php/src/Ui | 검색 adapter 미연결 상태를 표시한다. |
| 0537 | Add PHP recent changes page shell | PHP recent changes page shell을 추가한다. | php/src/Ui | 빈 상태와 필터 영역을 둔다. |
| 0538 | Add PHP login page shell | PHP login page shell을 추가한다. | php/src/Ui | 인증 구현 전 준비 화면이다. |
| 0539 | Add PHP permission denied page | PHP permission denied page를 추가한다. | php/src/Ui | ACL deny 상태를 표시한다. |
| 0540 | Add PHP CSRF token service | PHP CSRF token service를 추가한다. | php/src/Security, php/tests | 세션/서명 정책을 단순하게 둔다. |
| 0541 | Apply CSRF to PHP document forms | PHP 문서 폼에 CSRF를 적용한다. | php/src/Ui, php/tests | 잘못된 토큰은 저장하지 않는다. |
| 0542 | Add PHP form error summary component | PHP form error summary 컴포넌트를 추가한다. | php/src/Ui | 접근 가능한 오류 요약을 둔다. |
| 0543 | Add PHP flash message support | PHP flash message support를 추가한다. | php/src/Ui | redirect 후 성공 메시지 기반이다. |
| 0544 | Add PHP admin dashboard shell | PHP admin dashboard shell을 추가한다. | php/src/Ui | 시스템 상태/신고/감사 링크를 둔다. |
| 0545 | Add PHP audit log viewer shell | PHP audit log viewer shell을 추가한다. | php/src/Ui | 빈 상태와 필터 영역을 둔다. |
| 0546 | Add PHP admin report list shell | PHP admin report list shell을 추가한다. | php/src/Ui | 신고 목록 표시 기반이다. |
| 0547 | Add PHP block user form shell | PHP block user form shell을 추가한다. | php/src/Ui | 위험 작업 확인 영역을 둔다. |
| 0548 | Add PHP discussion page shell | PHP discussion page shell을 추가한다. | php/src/Ui | thread 없음 상태를 표시한다. |
| 0549 | Add PHP comment form shell | PHP comment form shell을 추가한다. | php/src/Ui | 권한 없음/로그인 필요 상태를 둔다. |
| 0550 | Add PHP UI navigation model | PHP UI navigation model을 추가한다. | php/src/Ui | active 상태와 권한별 표시 준비를 둔다. |
| 0551 | Add PHP responsive table component | PHP responsive table component를 추가한다. | php/src/Ui, php/public/static | 감사/최근 변경/관리자 목록에서 재사용한다. |
| 0552 | Add PHP pagination component | PHP pagination component를 추가한다. | php/src/Ui | query parameter 보존을 지원한다. |
| 0553 | Add PHP empty state component | PHP empty state component를 추가한다. | php/src/Ui | title/description/action 구조다. |
| 0554 | Add PHP UI security headers | PHP UI 보안 헤더를 추가한다. | php/src/Http | CSP, nosniff, frame options를 둔다. |
| 0555 | Extract PHP UI scripts to static files | PHP UI script를 static file로 분리한다. | php/public/static | inline script를 피한다. |
| 0556 | Add PHP print stylesheet | 문서 화면 print stylesheet를 추가한다. | php/public/static | nav/action 숨김을 둔다. |
| 0557 | Add PHP UI request id display | PHP UI request id 표시를 추가한다. | php/src/Ui | 운영 문의 추적 기반이다. |
| 0558 | Add PHP UI i18n placeholder | PHP UI i18n placeholder를 추가한다. | php/src/Ui | 기본 locale은 ko다. |
| 0559 | Add PHP UI snapshot fixtures | PHP UI HTML snapshot fixture를 추가한다. | php/tests/fixtures | layout/document form부터 시작한다. |
| 0560 | Add PHP UI phase QA checklist | PHP UI phase QA 체크리스트를 추가한다. | docs | 접근성, 보안, 모바일, 오류 상태를 포함한다. |
| 0561 | Add Python UI deprecation note | Python UI 직접 구현 보류/폐기 기준을 문서화한다. | docs | 최종 UI 기준은 PHP shared hosting으로 둔다. |
| 0562 | Add UI route parity matrix | Python/PHP UI route parity matrix를 추가한다. | docs | 최종적으로 PHP route를 canonical로 둔다. |
| 0563 | Add PHP document route integration tests | PHP document route 통합 테스트를 추가한다. | php/tests | create/view/edit/history 흐름을 검증한다. |
| 0564 | Add PHP admin route registration tests | PHP admin route 등록 테스트를 추가한다. | php/tests | admin/audit/reports/blocks를 확인한다. |
| 0565 | Add PHP auth route registration tests | PHP auth route 등록 테스트를 추가한다. | php/tests | login/logout placeholder를 확인한다. |
| 0566 | Add PHP UI mobile CSS tests | 모바일 CSS 존재 테스트를 추가한다. | php/tests | viewport와 media query를 확인한다. |
| 0567 | Add PHP UI XSS regression fixtures | UI XSS regression fixture를 추가한다. | php/tests/fixtures | title/source/comment/report에 적용한다. |
| 0568 | Add PHP UI permission state fixtures | UI 권한 상태 fixture를 추가한다. | php/tests/fixtures | anonymous/user/admin/blocked 상태를 둔다. |
| 0569 | Add PHP UI duplicate submit protection | 문서 폼 중복 제출 방지를 추가한다. | php/src/Security, php/tests | idempotency key 또는 one-time token을 둔다. |
| 0570 | Add PHP UI readiness gate | UI readiness gate 문서를 추가한다. | docs | 웹호스팅 배포 전 UI 완료 조건을 둔다. |
| 0571 | Add PHP search result component | PHP search result component를 추가한다. | php/src/Ui | snippet escape를 보장한다. |
| 0572 | Add PHP recent changes row component | PHP recent changes row component를 추가한다. | php/src/Ui | 문서명/사용자/요약/시간을 둔다. |
| 0573 | Add PHP audit row component | PHP audit row component를 추가한다. | php/src/Ui | event type/actor/target/time을 둔다. |
| 0574 | Add PHP admin danger confirmation component | PHP 위험 작업 확인 컴포넌트를 추가한다. | php/src/Ui | 대상과 작업명을 명확히 표시한다. |
| 0575 | Add PHP UI loading button state | PHP UI loading/disabled button state CSS를 추가한다. | php/public/static | 중복 클릭 방지 UX 기반이다. |
| 0576 | Add PHP UI no-JS fallback docs | no-JS fallback 정책을 문서화한다. | docs | 서버 렌더링 기본 원칙이다. |
| 0577 | Add PHP UI cache header policy | UI cache header 정책을 추가한다. | docs, php/src/Http | HTML과 static asset을 구분한다. |
| 0578 | Add PHP static asset cache headers | PHP static asset cache headers를 추가한다. | php/src/Http | hash 없는 파일은 짧은 캐시다. |
| 0579 | Add PHP UI performance budget docs | UI 성능 예산 문서를 추가한다. | docs | HTML/CSS/JS 크기 목표를 둔다. |
| 0580 | Add PHP UI performance budget test | UI 정적 자산 크기 budget 테스트를 추가한다. | php/tests | 큰 번들 도입을 방지한다. |
| 0581 | Add PHP document renderer adapter | PHP document renderer adapter를 추가한다. | php/src/Modules/Render, php/src/Ui | source->HTML 연결 지점만 둔다. |
| 0582 | Connect PHP render output to document view | document view에 render output을 연결한다. | php/src/Ui | unsafe HTML 정책을 테스트한다. |
| 0583 | Add PHP render fallback state | render 실패 fallback 상태를 추가한다. | php/src/Ui | source 표시 또는 오류 안내를 둔다. |
| 0584 | Add PHP editor preview placeholder | 편집 preview placeholder를 추가한다. | php/src/Ui | 실제 preview API는 후속이다. |
| 0585 | Add PHP UI audit event hook docs | UI 액션 audit hook 문서를 추가한다. | docs | create/edit/admin action을 포함한다. |
| 0586 | Add PHP UI audit hook placeholders | UI form action audit hook placeholder를 추가한다. | php/src | no-op audit recorder를 사용한다. |
| 0587 | Add PHP UI installer link policy | 설치 전/후 UI 링크 정책을 문서화한다. | docs | installer 노출 조건을 둔다. |
| 0588 | Add PHP install required page | 설치 필요 페이지를 추가한다. | php/src/Ui | DB 미설치 상태를 안내한다. |
| 0589 | Add PHP maintenance mode page | maintenance mode 페이지를 추가한다. | php/src/Ui | migration 중 안내 상태다. |
| 0590 | Add PHP UI operational diagnostics page | 운영 진단 페이지를 추가한다. | php/src/Ui | DB/schema/cache 상태 placeholder를 둔다. |
| 0591 | Add PHP UI logging policy docs | UI logging 정책을 문서화한다. | docs | 민감 정보 마스킹을 포함한다. |
| 0592 | Add PHP UI error page integration | 404/500 오류 페이지 연결을 추가한다. | php/src/Http, php/src/Ui | API JSON과 HTML을 구분한다. |
| 0593 | Add PHP API HTML accept negotiation | Accept header 협상 테스트를 추가한다. | php/tests | JSON/API와 HTML/UI 경계를 검증한다. |
| 0594 | Add PHP UI SEO basics | 기본 meta/title/canonical 정책을 추가한다. | php/src/Ui | 위키 문서 제목 중심이다. |
| 0595 | Add PHP UI robots policy docs | robots 정책 문서를 추가한다. | docs | 비공개/관리자 경로 차단을 다룬다. |
| 0596 | Add PHP UI sitemap placeholder | sitemap placeholder route를 추가한다. | php/src | 실제 목록 조회는 후속이다. |
| 0597 | Add PHP UI admin audit export placeholder | 감사 로그 export placeholder를 추가한다. | php/src/Ui | 실제 CSV는 후속이다. |
| 0598 | Add PHP UI backup page placeholder | 백업 페이지 placeholder를 추가한다. | php/src/Ui | shared hosting 운영을 고려한다. |
| 0599 | Add PHP UI restore warning page | 복구 경고 페이지를 추가한다. | php/src/Ui | 위험 작업 확인을 사용한다. |
| 0600 | Add UI phase summary | UI phase summary를 추가한다. | docs | 다음 shared hosting 단계 진입 조건을 요약한다. |
| 0601 | Add UI manual QA script | UI 수동 QA 스크립트를 추가한다. | docs | 홈/문서/관리자/모바일/오류 상태를 포함한다. |
| 0602 | Add UI route smoke command | UI route smoke command를 추가한다. | php/scripts | PHP built-in server 또는 direct handler를 사용한다. |
| 0603 | Add UI form smoke command | UI form smoke command를 추가한다. | php/scripts | create/edit csrf 흐름을 확인한다. |
| 0604 | Add UI ACL smoke command | UI ACL smoke command를 추가한다. | php/scripts | read/edit/admin deny 상태를 확인한다. |
| 0605 | Add UI DB smoke command | UI DB smoke command를 추가한다. | php/scripts | document create/view DB round-trip을 확인한다. |
| 0606 | Add UI static asset integrity docs | static asset integrity 정책을 문서화한다. | docs | 해시/버전 쿼리 정책을 둔다. |
| 0607 | Add UI asset version helper | asset version helper를 추가한다. | php/src/Ui | cache busting을 지원한다. |
| 0608 | Add UI deployment checklist | UI 배포 체크리스트를 추가한다. | docs | 파일 권한, cache, public path를 포함한다. |
| 0609 | Add UI rollback checklist | UI rollback 체크리스트를 추가한다. | docs | schema/UI 호환성을 다룬다. |
| 0610 | Add UI readiness report placeholder | UI readiness report placeholder를 추가한다. | docs | 운영 전 최종 보고서 기반이다. |

## Phase E: Shared Hosting Packaging and Installer, 0611-0670

목표: 일반 PHP 웹호스팅에 올릴 수 있는 파일 구조, 설치기, 운영 문서를 준비한다.

| ID | Task title | Goal | Scope | Notes |
|---|---|---|---|---|
| 0611 | Document shared hosting target baseline | 대상 웹호스팅 baseline을 문서화한다. | docs | PHP 버전, PDO, MariaDB, rewrite 지원을 명시한다. |
| 0612 | Add public docroot policy | public docroot 정책을 추가한다. | docs, php | public 밖에 설정/소스가 있어야 한다. |
| 0613 | Add htaccess front controller rules | `.htaccess` front controller 규칙을 추가한다. | php/public | Apache shared hosting 기본이다. |
| 0614 | Add nginx rewrite docs | nginx rewrite 문서를 추가한다. | docs | VPS 사용자를 위한 참고다. |
| 0615 | Add web config sample | 웹호스팅 설정 sample을 추가한다. | php/config | 민감 정보는 sample만 둔다. |
| 0616 | Add local config loader | local config loader를 추가한다. | php/src/App | 환경변수가 없어도 파일 설정을 읽는다. |
| 0617 | Add config file permission docs | config 파일 권한 문서를 추가한다. | docs | 웹에서 직접 노출되지 않게 한다. |
| 0618 | Add installer route gate | installer route gate를 추가한다. | php/src/Installer | 설치 완료 후 접근 차단한다. |
| 0619 | Add installer welcome page | installer welcome page를 추가한다. | php/src/Ui | 요구사항 체크 진입점이다. |
| 0620 | Add installer requirement check | installer requirement check를 추가한다. | php/src/Installer | PHP extensions, writable dirs를 확인한다. |
| 0621 | Add installer DB form | installer DB 설정 폼을 추가한다. | php/src/Ui | MariaDB DSN/user/password를 받는다. |
| 0622 | Add installer DB connection test | installer DB 연결 테스트를 추가한다. | php/src/Installer | 실제 schema 적용 전 확인한다. |
| 0623 | Add installer schema apply placeholder | installer schema apply placeholder를 추가한다. | php/src/Installer | dry-run/confirm 흐름만 둔다. |
| 0624 | Add installer admin account form | installer admin account form을 추가한다. | php/src/Ui | 최초 관리자 계정 생성 기반이다. |
| 0625 | Add installer completion page | installer completion page를 추가한다. | php/src/Ui | 설치 완료와 다음 조치를 안내한다. |
| 0626 | Add writable directories policy | writable directories 정책을 문서화한다. | docs | cache/uploads/logs를 분리한다. |
| 0627 | Add storage path config | storage path config를 추가한다. | php/src/App | shared hosting 경로 차이를 흡수한다. |
| 0628 | Add cache directory check | cache directory check를 추가한다. | php/src/Installer | 쓰기 가능 여부를 확인한다. |
| 0629 | Add upload directory check | upload directory check를 추가한다. | php/src/Installer | 향후 파일 기능 대비다. |
| 0630 | Add log directory check | log directory check를 추가한다. | php/src/Installer | fallback logging 기반이다. |
| 0631 | Add file permission diagnostics page | 파일 권한 진단 페이지를 추가한다. | php/src/Ui | 관리자 진단 화면과 연결한다. |
| 0632 | Add shared hosting session policy | shared hosting session 정책을 추가한다. | docs | PHP session/file/session DB 선택 기준을 둔다. |
| 0633 | Add PHP session adapter skeleton | PHP session adapter skeleton을 추가한다. | php/src/Security | login 단계와 연결 가능하게 둔다. |
| 0634 | Add cookie security policy | cookie 보안 정책을 문서화한다. | docs | secure, httponly, samesite 기준을 둔다. |
| 0635 | Add path traversal guard | path traversal guard를 추가한다. | php/src/Security, php/tests | config/storage 접근 안전장치다. |
| 0636 | Add web hosting mail policy | 웹호스팅 mail 정책을 문서화한다. | docs | SMTP/mail 함수 선택을 다룬다. |
| 0637 | Add email adapter skeleton | email adapter skeleton을 추가한다. | php/src/App | 알림은 후속 기능이다. |
| 0638 | Add backup download guard | backup download guard placeholder를 추가한다. | php/src/Security | 관리자 권한과 path guard를 요구한다. |
| 0639 | Add export directory policy | export directory 정책을 문서화한다. | docs | public 밖 저장을 기본으로 한다. |
| 0640 | Add deployment package manifest | deployment package manifest를 추가한다. | php | 배포 포함/제외 파일 목록을 둔다. |
| 0641 | Add package build script skeleton | package build script skeleton을 추가한다. | scripts | vendor 포함/미포함 모드를 구분한다. |
| 0642 | Add no-composer hosting docs | composer 없는 호스팅 배포 문서를 추가한다. | docs | vendor 사전 업로드 절차를 설명한다. |
| 0643 | Add composer hosting docs | composer 가능한 호스팅 배포 문서를 추가한다. | docs | install/update 절차를 설명한다. |
| 0644 | Add upgrade procedure docs | 업그레이드 절차 문서를 추가한다. | docs | 파일 교체, migration, cache clear를 포함한다. |
| 0645 | Add rollback procedure docs | rollback 절차 문서를 추가한다. | docs | DB backward compatibility 주의점을 둔다. |
| 0646 | Add maintenance mode toggle | maintenance mode toggle skeleton을 추가한다. | php/src/App | config 기반 on/off를 둔다. |
| 0647 | Add cache clear command | cache clear command skeleton을 추가한다. | php/scripts | 웹호스팅 CLI 부재 대안도 문서화한다. |
| 0648 | Add web cache clear page | web cache clear page placeholder를 추가한다. | php/src/Ui | 관리자만 접근한다. |
| 0649 | Add production error handling policy | production error handling 정책을 추가한다. | docs | 사용자 메시지와 로그 메시지를 분리한다. |
| 0650 | Add production error handler | production error handler skeleton을 추가한다. | php/src/App | debug off 기준이다. |
| 0651 | Add PHP log writer skeleton | PHP log writer skeleton을 추가한다. | php/src/App | file log fallback을 둔다. |
| 0652 | Add log redaction tests | log redaction 테스트를 추가한다. | php/tests | password/token 마스킹을 검증한다. |
| 0653 | Add shared hosting cron policy | shared hosting cron 정책을 문서화한다. | docs | jobs sync runner와 web trigger 대안을 둔다. |
| 0654 | Add web-triggered job runner guard | web-triggered job runner guard를 추가한다. | php/src/Jobs | secret token/rate limit 기반이다. |
| 0655 | Add job runner URL docs | job runner URL 문서를 추가한다. | docs | 호스팅 cron 설정 예시를 둔다. |
| 0656 | Add installer lock file policy | installer lock file 정책을 추가한다. | docs, php/src/Installer | 설치 완료 후 재실행 차단이다. |
| 0657 | Add environment diagnostics export | 환경 진단 export placeholder를 추가한다. | php/src/Ui | 민감 정보 제외를 테스트한다. |
| 0658 | Add shared hosting security checklist | shared hosting 보안 체크리스트를 추가한다. | docs | public path, config, installer, permissions를 포함한다. |
| 0659 | Add shared hosting performance checklist | shared hosting 성능 체크리스트를 추가한다. | docs | opcode cache, static cache, DB index를 다룬다. |
| 0660 | Add shared hosting QA checklist | shared hosting QA 체크리스트를 추가한다. | docs | 설치, 업그레이드, rollback, forms, admin을 포함한다. |
| 0661 | Add release notes template | release notes template를 추가한다. | docs | migration 필요 여부를 포함한다. |
| 0662 | Add version file | version file을 추가한다. | php | 앱 버전과 schema version을 분리한다. |
| 0663 | Add version display in admin diagnostics | 관리자 진단에 version 표시를 추가한다. | php/src/Ui | 운영 문의 추적용이다. |
| 0664 | Add compatibility report template | compatibility report template를 추가한다. | docs | PHP/MariaDB/hosting provider 결과를 기록한다. |
| 0665 | Add sample hosting provider checklist | hosting provider별 체크리스트 sample을 추가한다. | docs | cPanel/Plesk/plain FTP 기준이다. |
| 0666 | Add final Python to PHP cutover plan | Python에서 PHP로 최종 전환 계획을 추가한다. | docs | 데이터, route, config, rollback을 포함한다. |
| 0667 | Add post-cutover validation script | cutover 후 검증 스크립트 skeleton을 추가한다. | php/scripts | health, DB, document create/view를 확인한다. |
| 0668 | Add production readiness report placeholder | production readiness report placeholder를 추가한다. | docs | 최종 검수 보고서 기반이다. |
| 0669 | Add hosting phase QA checklist | hosting phase QA 체크리스트를 추가한다. | docs | installer/package/security/rollback을 점검한다. |
| 0670 | Add 0351-0670 completion summary | 0351-0670 완료 요약 문서를 추가한다. | docs | 남은 기능과 위험을 다음 큐로 넘긴다. |

## Next recommended ranges

- 0671-0740: PHP 기능 parity 심화(parser/render/search/discussion/admin 실제 구현).
- 0741-0800: 운영 보안, 백업/복구, 계정/권한 실사용 UX 강화.
- 0801-0850: 성능, 대용량 문서, migration hardening, 호스팅 사업자별 호환성 검증.
