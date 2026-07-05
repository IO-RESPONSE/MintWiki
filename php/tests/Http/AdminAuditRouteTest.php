<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0698에서 등록하는 `GET /admin/audit` route의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다(0697
 * AdminDashboardRouteTest.php와 동일한 방식) — index.php는 재사용 가능한
 * 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 비로그인(익명) 사용자는 GET /admin/audit에서 `/login`으로 302를 받는다.
 * (2) 로그인했지만 관리자 권한이 없는 사용자는 403(PermissionDeniedPage)을 받는다.
 * (3) 관리자는 200으로 AuditViewerPage를 받고, `audit_event` 테이블의 이벤트가
 *     occurred_at 내림차순으로 행 렌더링되며, 스킨 `Layout`의 header/footer를
 *     포함해야 한다.
 * (4) 이벤트가 없으면 빈 상태 메시지를 안전하게 렌더링한다.
 * (5) `$accountRepository`가 없으면(DB 미설정/오류) GET /admin/audit은 항상
 *     `/login`으로 302한다(0674 계약과 동일).
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
use MintWiki\Acl\Permission;
use MintWiki\Acl\SubjectType;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\AuditViewerPage;
use MintWiki\Ui\Layout;
use MintWiki\User\AccountRepository;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET /admin/audit` 핸들러와 동일한 등록
 * 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_admin_audit_route(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService,
    ?PDO $pdo
): void {
    $router->register('GET', '/admin/audit', static function () use ($accountRepository, $sessionAdapter, $aclService, $pdo): Response {
        $layout = new Layout();

        if ($accountRepository === null) {
            return new Response(302, ['Location' => '/login']);
        }

        $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
        $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

        $gateResponse = $adminAccessGate->authorize();
        if ($gateResponse !== null) {
            return $gateResponse;
        }

        $auditEvents = [];
        if ($pdo !== null) {
            try {
                $auditEvents = (new RecentAuditEventsQuery($pdo))->listRecentEvents();
            } catch (\Throwable $exception) {
                $auditEvents = [];
            }
        }

        $auditViewerPage = new AuditViewerPage(null, $layout);

        return Response::html($auditViewerPage->render($auditEvents));
    });
}

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
$auditEventSql = file_get_contents(__DIR__ . '/../../../db/schema/audit_event.sql');
if ($accountSql === false || $aclNamespaceRuleSql === false || $auditEventSql === false) {
    fwrite(STDERR, "db/schema/account.sql, acl_namespace_rule.sql 또는 audit_event.sql을 읽을 수 없습니다.\n");
    exit(1);
}

try {
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);
    $pdo->exec($aclNamespaceRuleSql);
    $pdo->exec($auditEventSql);

    $accountRepository = new AccountRepository($pdo);
    $adminId = $accountRepository->create('admin', password_hash('irrelevant', PASSWORD_DEFAULT));
    $regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));

    $aclRepository = new AclPdoRepository($pdo);
    $aclRepository->grantNamespacePermission(
        NamespaceAclDefaults::DEFAULT_NAMESPACE,
        SubjectType::User,
        Permission::Admin,
        Effect::Allow,
        $adminId
    );

    $namespaceAclDefaults = new NamespaceAclDefaults();
    $namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
    $namespaceAclDefaults->register(
        NamespaceAclDefaults::DEFAULT_NAMESPACE,
        $aclRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE)
    );
    $aclService = new AclService($namespaceAclDefaults);

    $sessionAdapter = new PhpSessionAdapter();

    // ------------------------------------------------------------------
    // (4) 이벤트가 없는 상태 — 빈 상태를 안전하게 렌더링해야 한다.
    // ------------------------------------------------------------------
    $emptyRouter = new Router();
    mintwiki_register_admin_audit_route($emptyRouter, $accountRepository, $sessionAdapter, $aclService, $pdo);

    $_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
    $emptyResponse = $emptyRouter->match(new Request('GET', '/admin/audit'))();
    if ($emptyResponse->status() !== 200) {
        $failures[] = '(4) 이벤트가 없는 관리자의 GET /admin/audit은 200이어야 하는데 ' . $emptyResponse->status() . '이었다.';
    }
    if (!str_contains($emptyResponse->body(), '감사 로그가 없습니다.')) {
        $failures[] = '(4) 이벤트가 없으면 빈 상태 메시지를 표시해야 한다.';
    }

    // ------------------------------------------------------------------
    // audit_event 이벤트 삽입 (occurred_at 내림차순 검증용)
    // ------------------------------------------------------------------
    $insertStatement = $pdo->prepare(
        'INSERT INTO audit_event (id, category, action, entity_id, related_entity_id, actor_id, occurred_at) '
        . 'VALUES (:id, :category, :action, :entity_id, NULL, :actor_id, :occurred_at)'
    );
    $insertStatement->execute([
        'id' => 'evt-old',
        'category' => 'acl',
        'action' => 'rule_added',
        'entity_id' => 'rule-1',
        'actor_id' => $adminId,
        'occurred_at' => '2026-01-01 00:00:00',
    ]);
    $insertStatement->execute([
        'id' => 'evt-new',
        'category' => 'discussion',
        'action' => 'thread_created',
        'entity_id' => 'thread-1',
        'actor_id' => null,
        'occurred_at' => '2026-06-01 00:00:00',
    ]);

    $router = new Router();
    mintwiki_register_admin_audit_route($router, $accountRepository, $sessionAdapter, $aclService, $pdo);

    // (1) 비로그인(익명) → /login으로 302.
    $_SESSION = [];
    $anonResponse = $router->match(new Request('GET', '/admin/audit'))();
    if ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(1) 비로그인 사용자의 GET /admin/audit은 /login으로 302여야 하는데 status=' . $anonResponse->status()
            . ', Location=' . ($anonResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    // (2) 로그인했으나 관리자가 아님 → 403.
    $_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
    $regularResponse = $router->match(new Request('GET', '/admin/audit'))();
    if ($regularResponse->status() !== 403) {
        $failures[] = '(2) 비관리자 사용자의 GET /admin/audit은 403이어야 하는데 ' . $regularResponse->status() . '이었다.';
    }
    if (!str_contains($regularResponse->body(), '권한 없음')) {
        $failures[] = '(2) 비관리자 거부 응답은 PermissionDeniedPage를 보여줘야 한다.';
    }

    // (3) 관리자 → 200으로 감사 로그 표. occurred_at 내림차순으로 렌더링되어야 한다.
    $_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
    $adminResponse = $router->match(new Request('GET', '/admin/audit'))();
    if ($adminResponse->status() !== 200) {
        $failures[] = '(3) 관리자의 GET /admin/audit은 200이어야 하는데 ' . $adminResponse->status() . '이었다.';
    }

    $adminBody = $adminResponse->body();
    if (!str_contains($adminBody, '<h1>감사 로그</h1>')) {
        $failures[] = '(3) 감사 로그 page가 h1으로 "감사 로그"를 표시해야 한다.';
    }
    if (!str_contains($adminBody, '<table class="audit-table">')) {
        $failures[] = '(3) 이벤트가 있으면 AuditRow 표를 렌더링해야 한다.';
    }
    if (!str_contains($adminBody, 'discussion.thread_created')) {
        $failures[] = '(3) 가장 최근(occurred_at 최대) 이벤트가 표에 포함되어야 한다.';
    }
    if (!str_contains($adminBody, 'acl.rule_added')) {
        $failures[] = '(3) 더 오래된 이벤트도 표에 포함되어야 한다.';
    }

    $newPosition = strpos($adminBody, 'discussion.thread_created');
    $oldPosition = strpos($adminBody, 'acl.rule_added');
    if ($newPosition === false || $oldPosition === false || $newPosition > $oldPosition) {
        $failures[] = '(3) 이벤트는 occurred_at 내림차순(최근 이벤트가 먼저)으로 렌더링되어야 한다.';
    }

    if (!str_contains($adminBody, '<!doctype html>')) {
        $failures[] = '(3) 감사 로그 응답이 스킨 Layout의 doctype을 포함해야 한다.';
    }
    if (!str_contains($adminBody, '<header>')) {
        $failures[] = '(3) 감사 로그 응답이 스킨 Layout의 header를 포함해야 한다.';
    }
    if (!str_contains($adminBody, '<footer>')) {
        $failures[] = '(3) 감사 로그 응답이 스킨 Layout의 footer를 포함해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(4) in-process 테스트 실패: ' . $e->getMessage();
}

// (5) $accountRepository가 없으면(DB 미설정) GET /admin/audit은 항상 /login으로 302해야 한다.
try {
    $_SESSION = [SessionUserResolver::SESSION_KEY => 'irrelevant-account-id'];
    $unconfiguredRouter = new Router();
    mintwiki_register_admin_audit_route($unconfiguredRouter, null, new PhpSessionAdapter(), new AclService(), null);

    $unconfiguredResponse = $unconfiguredRouter->match(new Request('GET', '/admin/audit'))();
    if ($unconfiguredResponse->status() !== 302 || ($unconfiguredResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(5) DB 미설정 상태의 GET /admin/audit은 /login으로 302여야 하는데 status=' . $unconfiguredResponse->status()
            . ', Location=' . ($unconfiguredResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(5) DB 미설정 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /admin/audit route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /admin/audit route 테스트 통과.\n");
exit(0);
