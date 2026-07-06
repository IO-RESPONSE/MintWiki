<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0717에서 등록하는
 * `GET /admin/diagnostics/export`를 확인하는 smoke test. phpunit 없이 `php`
 * CLI만으로 실행된다(0716 `BackupDownloadRouteTest.php`와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직(관리자 게이트 +
 * `OperationalDiagnosticsCollector::collectExportSnapshot()` +
 * `SensitiveDiagnosticsFilter` + 감사 기록 포함)을 Router에 그대로
 * 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 관리자 다운로드는 200과 Content-Type: application/json, attachment
 *     Content-Disposition, 그리고 파싱 가능한 JSON 본문을 반환한다.
 * (2) DB 자격 증명(mariadb_password/database_url)이 config에 설정되어
 *     있어도 export 본문에는 그 값이 전혀 포함되지 않는다.
 * (3) 익명은 `/login`으로 302, 관리자가 아닌 로그인 사용자는 403을 반환한다.
 * (4) DB가 미설정(`$pdo === null`)이어도 500/치명적 오류 없이 200과
 *     "미설정" 상태를 담은 스냅샷을 반환한다.
 * (5) 다운로드 성공 시 module=diagnostics, action=exported 감사 이벤트가
 *     기록된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\Effect;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\App\ConfigLoader;
use MintWiki\App\OperationalDiagnosticsCollector;
use MintWiki\App\SensitiveDiagnosticsFilter;
use MintWiki\App\StoragePathConfig;
use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\PdoAuditRecorder;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\User\AccountRepository;

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_diagnostics_export_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return [AclSubjectType::User, $currentUser->id()];
        }
    }

    return [AclSubjectType::Anonymous, null];
}

/**
 * `public/index.php`가 0717에서 등록하는 `GET /admin/diagnostics/export`
 * 핸들러와 동일한 등록 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_diagnostics_export_route(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService,
    OperationalDiagnosticsCollector $collector,
    PdoAuditRecorder $auditRecorder
): void {
    $router->register('GET', '/admin/diagnostics/export', static function () use (
        $accountRepository,
        $sessionAdapter,
        $aclService,
        $collector,
        $auditRecorder
    ): Response {
        if ($accountRepository === null) {
            return new Response(302, ['Location' => '/login']);
        }

        $gateResponse = (new AdminAccessGate($aclService, new SessionUserResolver($sessionAdapter, $accountRepository)))->authorize();
        if ($gateResponse !== null) {
            return $gateResponse;
        }

        $snapshot = SensitiveDiagnosticsFilter::filter($collector->collectExportSnapshot());
        $exportFilename = 'mintwiki-diagnostics-' . gmdate('Ymd-His') . '.json';

        [$subjectType, $subjectId] = mintwiki_diagnostics_export_test_resolve_subject($accountRepository, $sessionAdapter);
        $auditRecorder->record(new AuditEvent(
            id: bin2hex(random_bytes(16)),
            module: 'diagnostics',
            action: 'exported',
            occurredAt: new \DateTimeImmutable('now'),
            actorId: $subjectType === AclSubjectType::Anonymous ? 'anonymous' : $subjectId,
            metadata: ['entity_id' => $exportFilename]
        ));

        $body = json_encode($snapshot, JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR) . "\n";

        return new Response(200, [
            'Content-Type' => 'application/json',
            'Content-Disposition' => 'attachment; filename="' . $exportFilename . '"',
            'Content-Length' => (string) strlen($body),
            'X-Content-Type-Options' => 'nosniff',
        ], $body);
    });
}

function mintwiki_diagnostics_export_test_login(?string $accountId): void
{
    $_SESSION = [];
    if ($accountId !== null) {
        $_SESSION[SessionUserResolver::SESSION_KEY] = $accountId;
    }
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
$auditEventSql = file_get_contents(__DIR__ . '/../../../db/schema/audit_event.sql');
$schemaVersionSql = file_get_contents(__DIR__ . '/../../../db/schema/schema_version.sql');

if ($accountSql === false || $aclNamespaceRuleSql === false || $auditEventSql === false || $schemaVersionSql === false) {
    fwrite(STDERR, "필수 schema fixture를 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($accountSql);
$pdo->exec($aclNamespaceRuleSql);
$pdo->exec($auditEventSql);
$pdo->exec($schemaVersionSql);
$pdo->exec("INSERT INTO schema_version (version, applied_at) VALUES ('0717', '2026-07-06 00:00:00')");

$accountRepository = new AccountRepository($pdo);
$adminId = $accountRepository->create('diag-admin', password_hash('irrelevant', PASSWORD_DEFAULT));
$regularId = $accountRepository->create('diag-regular', password_hash('irrelevant', PASSWORD_DEFAULT));

$aclRepository = new AclPdoRepository($pdo);
$aclRepository->grantNamespacePermission(NamespaceAclDefaults::DEFAULT_NAMESPACE, AclSubjectType::User, AclPermission::Admin, Effect::Allow, $adminId);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, $aclRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE));
$aclService = new AclService($namespaceAclDefaults);

$sessionAdapter = new PhpSessionAdapter();
$auditRecorder = new PdoAuditRecorder($pdo);
$auditQuery = new RecentAuditEventsQuery($pdo);

$cacheDir = sys_get_temp_dir() . '/mintwiki-diagnostics-export-test-' . getmypid();
@mkdir($cacheDir . '/cache', 0775, true);

// DB 자격 증명(비밀번호/DSN)이 config에 설정된 상태에서도 export가 그 값을
// 담지 않는지 확인하기 위해 일부러 민감한 값을 채운 ConfigLoader를 쓴다.
$configLoaderWithSecrets = new ConfigLoader([
    'database_url' => 'mysql://wiki_user:super-secret-password@localhost:3306/wiki_engine',
    'mariadb_password' => 'super-secret-password',
]);
$storagePathConfig = new StoragePathConfig(new ConfigLoader([]), $cacheDir);
$collector = new OperationalDiagnosticsCollector($pdo, 'connected', $configLoaderWithSecrets, $storagePathConfig, '1.2.3');

$router = new Router();
mintwiki_register_diagnostics_export_route($router, $accountRepository, $sessionAdapter, $aclService, $collector, $auditRecorder);

// (1) 관리자 다운로드는 200 + JSON 헤더/본문.
mintwiki_diagnostics_export_test_login($adminId);
$adminResponse = $router->match(new Request('GET', '/admin/diagnostics/export'))();
if ($adminResponse->status() !== 200) {
    $failures[] = "(1) 관리자 export 다운로드는 200이어야 하는데 {$adminResponse->status()}이었다.";
}
if (($adminResponse->headers()['Content-Type'] ?? null) !== 'application/json') {
    $failures[] = '(1) export 응답의 Content-Type은 application/json이어야 한다.';
}
if (!str_starts_with($adminResponse->headers()['Content-Disposition'] ?? '', 'attachment; filename="mintwiki-diagnostics-')) {
    $failures[] = '(1) export 응답의 Content-Disposition은 attachment + 파일명이어야 한다.';
}

$decoded = json_decode($adminResponse->body(), true);
if (!is_array($decoded)) {
    $failures[] = '(1) export 응답 본문이 유효한 JSON 배열로 파싱되어야 한다.';
} else {
    if (($decoded['db_status'] ?? null) !== '연결됨') {
        $failures[] = '(1) export 스냅샷의 db_status가 연결 상태를 반영해야 한다.';
    }
    if (($decoded['schema_migration'] ?? null) !== '0717') {
        $failures[] = '(1) export 스냅샷의 schema_migration이 최신 스키마 버전을 반영해야 한다.';
    }
    if (($decoded['app_version'] ?? null) !== '1.2.3') {
        $failures[] = '(1) export 스냅샷의 app_version이 주입한 버전이어야 한다.';
    }
}

// (2) DB 비밀번호/DSN 자격 증명이 export 본문에 전혀 없어야 한다.
if (str_contains($adminResponse->body(), 'super-secret-password')) {
    $failures[] = '(2) export 응답 본문에 DB 비밀번호가 포함되면 안 된다.';
}
if (str_contains($adminResponse->body(), 'wiki_user')) {
    $failures[] = '(2) export 응답 본문에 DB DSN 자격 증명이 포함되면 안 된다.';
}

// (3) 익명은 /login으로 302.
mintwiki_diagnostics_export_test_login(null);
$anonResponse = $router->match(new Request('GET', '/admin/diagnostics/export'))();
if ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(3) 익명 사용자는 /login으로 302여야 한다.';
}

// (3) 관리자가 아닌 로그인 사용자는 403.
mintwiki_diagnostics_export_test_login($regularId);
$regularResponse = $router->match(new Request('GET', '/admin/diagnostics/export'))();
if ($regularResponse->status() !== 403) {
    $failures[] = "(3) 비관리자 사용자는 403이어야 하는데 {$regularResponse->status()}이었다.";
}

// (4) DB가 미설정이어도 200과 안전한 "미설정" 상태를 반환한다.
$unconfiguredCollector = new OperationalDiagnosticsCollector(null, 'unconfigured', new ConfigLoader([]), $storagePathConfig, '1.2.3');
$unconfiguredRouter = new Router();
mintwiki_register_diagnostics_export_route($unconfiguredRouter, $accountRepository, $sessionAdapter, $aclService, $unconfiguredCollector, $auditRecorder);
mintwiki_diagnostics_export_test_login($adminId);
$unconfiguredResponse = $unconfiguredRouter->match(new Request('GET', '/admin/diagnostics/export'))();
if ($unconfiguredResponse->status() !== 200) {
    $failures[] = "(4) DB 미설정 상태에서도 export는 200이어야 하는데 {$unconfiguredResponse->status()}이었다.";
}
$unconfiguredDecoded = json_decode($unconfiguredResponse->body(), true);
if (!is_array($unconfiguredDecoded) || ($unconfiguredDecoded['db_status'] ?? null) !== '미설정') {
    $failures[] = '(4) DB 미설정 상태의 export 스냅샷은 db_status="미설정"이어야 한다.';
}

// (5) 다운로드 성공 시 감사 이벤트가 기록된다.
mintwiki_diagnostics_export_test_login($adminId);
$eventCountBeforeExport = count($auditQuery->listRecentEvents());
$router->match(new Request('GET', '/admin/diagnostics/export'))();
$eventsAfterExport = $auditQuery->listRecentEvents();
if (count($eventsAfterExport) !== $eventCountBeforeExport + 1) {
    $failures[] = '(5) export 성공 후 감사 이벤트가 정확히 1건 추가되어야 한다.';
} else {
    $exportedEvent = null;
    foreach ($eventsAfterExport as $candidate) {
        if ($candidate->action() === 'exported') {
            $exportedEvent = $candidate;
        }
    }
    if ($exportedEvent === null || $exportedEvent->category() !== 'diagnostics') {
        $failures[] = '(5) export 감사 이벤트는 category=diagnostics, action=exported여야 한다.';
    } elseif ($exportedEvent->actorId() !== $adminId) {
        $failures[] = '(5) export 감사 이벤트의 actor_id는 로그인한 관리자 계정 id여야 한다.';
    }
}

@rmdir($cacheDir . '/cache');
@rmdir($cacheDir);

if ($failures !== []) {
    fwrite(STDERR, "GET /admin/diagnostics/export 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /admin/diagnostics/export 테스트 통과.\n");
exit(0);
