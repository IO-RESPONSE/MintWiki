<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0716에서 등록하는
 * `GET /admin/backup/download/{name}`을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다(0715 `DocumentDeleteRouteTest.php`와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직(0696 관리자
 * 게이트 + listBackups() 화이트리스트 + 감사 기록 포함)을 Router에 그대로
 * 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 유효한 백업 파일 다운로드는 200과 Content-Type/Content-Disposition/
 *     Content-Length 헤더, 그리고 파일 본문을 그대로 반환한다.
 * (2) 경로 traversal(`../`)이나 목록에 없는 파일명, 존재하지 않는 파일은
 *     404를 반환한다.
 * (3) 익명은 `/login`으로 302, 관리자가 아닌 로그인 사용자는 403을 반환한다.
 * (4) 다운로드 성공 시 module=backup, action=downloaded 감사 이벤트가
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
use MintWiki\Admin\FileBackupRunner;
use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\PdoAuditRecorder;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\ErrorPage;
use MintWiki\User\AccountRepository;

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_backup_download_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
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
 * `public/index.php`가 0716에서 등록하는 `GET /admin/backup/download/{name}`
 * 핸들러와 동일한 등록 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_backup_download_route(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService,
    FileBackupRunner $backupRunner,
    PdoAuditRecorder $auditRecorder
): void {
    $router->register('GET', '/admin/backup/download/{name}', static function (array $params) use (
        $accountRepository,
        $sessionAdapter,
        $aclService,
        $backupRunner,
        $auditRecorder
    ): Response {
        if ($accountRepository === null) {
            return new Response(302, ['Location' => '/login']);
        }

        $gateResponse = (new AdminAccessGate($aclService, new SessionUserResolver($sessionAdapter, $accountRepository)))->authorize();
        if ($gateResponse !== null) {
            return $gateResponse;
        }

        $requestedName = rawurldecode($params['name'] ?? '');
        $path = $backupRunner->resolveBackupPath($requestedName);

        if ($path === null) {
            return Response::html((new ErrorPage())->renderNotFound('/admin/backup/download/' . $requestedName), 404);
        }

        $fileSize = filesize($path);
        if ($fileSize === false) {
            return Response::html((new ErrorPage())->renderNotFound('/admin/backup/download/' . $requestedName), 404);
        }

        $contentType = preg_match('/\.json\z/i', $requestedName) === 1 ? 'application/json' : 'application/octet-stream';

        [$subjectType, $subjectId] = mintwiki_backup_download_test_resolve_subject($accountRepository, $sessionAdapter);
        $auditRecorder->record(new AuditEvent(
            id: bin2hex(random_bytes(16)),
            module: 'backup',
            action: 'downloaded',
            occurredAt: new \DateTimeImmutable('now'),
            actorId: $subjectType === AclSubjectType::Anonymous ? 'anonymous' : $subjectId,
            metadata: ['entity_id' => $requestedName]
        ));

        return Response::download($path, $requestedName, $contentType, $fileSize);
    });
}

function mintwiki_backup_download_test_login(?string $accountId): void
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

if ($accountSql === false || $aclNamespaceRuleSql === false || $auditEventSql === false) {
    fwrite(STDERR, "필수 schema fixture를 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($accountSql);
$pdo->exec($aclNamespaceRuleSql);
$pdo->exec($auditEventSql);

$accountRepository = new AccountRepository($pdo);
$adminId = $accountRepository->create('backup-admin', password_hash('irrelevant', PASSWORD_DEFAULT));
$regularId = $accountRepository->create('backup-regular', password_hash('irrelevant', PASSWORD_DEFAULT));

$aclRepository = new AclPdoRepository($pdo);
$aclRepository->grantNamespacePermission(NamespaceAclDefaults::DEFAULT_NAMESPACE, AclSubjectType::User, AclPermission::Admin, Effect::Allow, $adminId);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, $aclRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE));
$aclService = new AclService($namespaceAclDefaults);

$sessionAdapter = new PhpSessionAdapter();
$auditRecorder = new PdoAuditRecorder($pdo);
$auditQuery = new RecentAuditEventsQuery($pdo);

$backupDirectory = sys_get_temp_dir() . '/mintwiki-backup-download-test-' . getmypid();
@mkdir($backupDirectory, 0775, true);
$validBackupName = 'mintwiki-backup-20260706-000000-abcd1234.json';
$backupContent = json_encode(['app' => 'MintWiki', 'created_at' => '2026-07-06T00:00:00Z', 'type' => 'metadata-only'], JSON_PRETTY_PRINT) . "\n";
file_put_contents($backupDirectory . '/' . $validBackupName, $backupContent);
// listBackups() 화이트리스트에 포함되지 않는, 백업 디렉터리 밖의 파일.
$outsideFile = sys_get_temp_dir() . '/mintwiki-backup-download-test-outside-' . getmypid() . '.json';
file_put_contents($outsideFile, 'secret');

$backupRunner = new FileBackupRunner($backupDirectory);

$router = new Router();
mintwiki_register_backup_download_route($router, $accountRepository, $sessionAdapter, $aclService, $backupRunner, $auditRecorder);

// (1) 유효한 백업 파일 다운로드는 200 + 올바른 헤더 + 본문.
mintwiki_backup_download_test_login($adminId);
$validResponse = $router->match(new Request('GET', '/admin/backup/download/' . $validBackupName))();
if ($validResponse->status() !== 200) {
    $failures[] = "(1) 유효한 백업 다운로드는 200이어야 하는데 {$validResponse->status()}이었다.";
}
if (($validResponse->headers()['Content-Type'] ?? null) !== 'application/json') {
    $failures[] = '(1) .json 백업의 Content-Type은 application/json이어야 한다.';
}
if (!str_contains($validResponse->headers()['Content-Disposition'] ?? '', 'attachment; filename="' . $validBackupName . '"')) {
    $failures[] = '(1) Content-Disposition 헤더에 attachment와 파일명이 있어야 한다.';
}
if (($validResponse->headers()['Content-Length'] ?? null) !== (string) strlen($backupContent)) {
    $failures[] = '(1) Content-Length 헤더가 실제 파일 크기와 일치해야 한다.';
}
if ($validResponse->streamFilePath() !== $backupDirectory . '/' . $validBackupName) {
    $failures[] = '(1) 응답이 실제 백업 파일 경로를 스트리밍 대상으로 가리켜야 한다.';
}
if (file_get_contents($validResponse->streamFilePath()) !== $backupContent) {
    $failures[] = '(1) 스트리밍 대상 파일의 내용이 실제 백업 내용과 같아야 한다.';
}

// (2) 경로 traversal은 404.
$traversalResponse = $router->match(new Request('GET', '/admin/backup/download/' . rawurlencode('../outside.json')))();
if ($traversalResponse->status() !== 404) {
    $failures[] = "(2) 경로 traversal 요청은 404여야 하는데 {$traversalResponse->status()}이었다.";
}

// (2) 목록(listBackups())에 없는 파일명은 404 — 백업 디렉터리 밖 파일의 basename을 그대로 요청.
$notListedResponse = $router->match(new Request('GET', '/admin/backup/download/' . basename($outsideFile)))();
if ($notListedResponse->status() !== 404) {
    $failures[] = "(2) 목록에 없는 파일명은 404여야 하는데 {$notListedResponse->status()}이었다.";
}

// (2) 존재하지 않는 파일명은 404.
$missingResponse = $router->match(new Request('GET', '/admin/backup/download/mintwiki-backup-missing.json'))();
if ($missingResponse->status() !== 404) {
    $failures[] = "(2) 존재하지 않는 백업 파일은 404여야 하는데 {$missingResponse->status()}이었다.";
}

// (3) 익명은 /login으로 302.
mintwiki_backup_download_test_login(null);
$anonResponse = $router->match(new Request('GET', '/admin/backup/download/' . $validBackupName))();
if ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(3) 익명 사용자는 /login으로 302여야 한다.';
}

// (3) 관리자가 아닌 로그인 사용자는 403.
mintwiki_backup_download_test_login($regularId);
$regularResponse = $router->match(new Request('GET', '/admin/backup/download/' . $validBackupName))();
if ($regularResponse->status() !== 403) {
    $failures[] = "(3) 비관리자 사용자는 403이어야 하는데 {$regularResponse->status()}이었다.";
}

// (4) 다운로드 성공 시 감사 이벤트가 기록된다.
$eventCountBeforeDownload = count($auditQuery->listRecentEvents());
mintwiki_backup_download_test_login($adminId);
$router->match(new Request('GET', '/admin/backup/download/' . $validBackupName))();
$eventsAfterDownload = $auditQuery->listRecentEvents();
if (count($eventsAfterDownload) !== $eventCountBeforeDownload + 1) {
    $failures[] = '(4) 다운로드 성공 후 감사 이벤트가 정확히 1건 추가되어야 한다.';
} else {
    $downloadedEvent = null;
    foreach ($eventsAfterDownload as $candidate) {
        if ($candidate->action() === 'downloaded') {
            $downloadedEvent = $candidate;
        }
    }
    if ($downloadedEvent === null || $downloadedEvent->category() !== 'backup') {
        $failures[] = '(4) 다운로드 감사 이벤트는 category=backup, action=downloaded여야 한다.';
    } elseif ($downloadedEvent->actorId() !== $adminId) {
        $failures[] = '(4) 다운로드 감사 이벤트의 actor_id는 로그인한 관리자 계정 id여야 한다.';
    }
}

@unlink($backupDirectory . '/' . $validBackupName);
@rmdir($backupDirectory);
@unlink($outsideFile);

if ($failures !== []) {
    fwrite(STDERR, "GET /admin/backup/download/{name} 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /admin/backup/download/{name} 테스트 통과.\n");
exit(0);
