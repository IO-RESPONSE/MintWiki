<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0697에서 등록하는 `GET /admin` route의 동작을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다(0686
 * LoginRouteTest.php와 동일한 방식) — index.php는 재사용 가능한 모듈이
 * 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 비로그인(익명) 사용자는 GET /admin에서 `/login`으로 302를 받는다.
 * (2) 로그인했지만 관리자 권한(acl_namespace_rule의 admin allow 규칙)이
 *     없는 사용자는 403(PermissionDeniedPage)을 받는다.
 * (3) 관리자는 200으로 AdminDashboardPage를 받고, 그 안에 관리 하위 화면
 *     (감사 로그/신고/사용자 차단/유지보수/백업/복원/진단) 링크와 스킨
 *     `Layout`의 header/footer/sidebar 마크업이 포함되어야 한다.
 * (4) `$accountRepository`가 없으면(DB 미설정/오류) GET /admin은 세션을
 *     복원할 수 없으므로 항상 `/login`으로 302한다(0674 계약과 동일).
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
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\AdminDashboardPage;
use MintWiki\Ui\Layout;
use MintWiki\User\AccountRepository;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET /admin` 핸들러와 동일한 등록 로직을
 * 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_admin_route(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService
): void {
    $router->register('GET', '/admin', static function () use ($accountRepository, $sessionAdapter, $aclService): Response {
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

        $adminDashboardPage = new AdminDashboardPage(null, $layout);

        return Response::html($adminDashboardPage->render());
    });
}

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
if ($accountSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/account.sql 또는 db/schema/acl_namespace_rule.sql을 읽을 수 없습니다.\n");
    exit(1);
}

try {
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);
    $pdo->exec($aclNamespaceRuleSql);

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
    $router = new Router();
    mintwiki_register_admin_route($router, $accountRepository, $sessionAdapter, $aclService);

    // (1) 비로그인(익명) → /login으로 302.
    $_SESSION = [];
    $anonResponse = $router->match(new Request('GET', '/admin'))();
    if ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(1) 비로그인 사용자의 GET /admin은 /login으로 302여야 하는데 status=' . $anonResponse->status()
            . ', Location=' . ($anonResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    // (2) 로그인했으나 관리자가 아님 → 403.
    $_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
    $regularResponse = $router->match(new Request('GET', '/admin'))();
    if ($regularResponse->status() !== 403) {
        $failures[] = '(2) 비관리자 사용자의 GET /admin은 403이어야 하는데 ' . $regularResponse->status() . '이었다.';
    }
    if (!str_contains($regularResponse->body(), '권한 없음')) {
        $failures[] = '(2) 비관리자 거부 응답은 PermissionDeniedPage를 보여줘야 한다.';
    }

    // (3) 관리자 → 200으로 대시보드 렌더. 하위 화면 링크와 스킨 마크업을 포함해야 한다.
    $_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
    $adminResponse = $router->match(new Request('GET', '/admin'))();
    if ($adminResponse->status() !== 200) {
        $failures[] = '(3) 관리자의 GET /admin은 200이어야 하는데 ' . $adminResponse->status() . '이었다.';
    }

    $adminBody = $adminResponse->body();
    if (!str_contains($adminBody, '<h1>관리자 대시보드</h1>')) {
        $failures[] = '(3) 관리자 대시보드가 h1으로 "관리자 대시보드"를 표시해야 한다.';
    }

    $expectedSubScreenLinks = [
        '/admin/audit' => '감사 로그',
        '/admin/reports' => '신고',
        '/admin/users/block' => '사용자 차단',
        '/admin/maintenance' => '유지보수',
        '/admin/backup' => '백업',
        '/admin/restore' => '복원',
        '/admin/diagnostics' => '진단',
    ];
    foreach ($expectedSubScreenLinks as $href => $label) {
        if (!str_contains($adminBody, '<a href="' . $href . '">' . $label . '</a>')) {
            $failures[] = "(3) 관리자 대시보드가 하위 화면 링크 {$href}({$label})를 포함해야 한다.";
        }
    }

    if (!str_contains($adminBody, '<!doctype html>')) {
        $failures[] = '(3) 관리자 대시보드 응답이 스킨 Layout의 doctype을 포함해야 한다.';
    }
    if (!str_contains($adminBody, '<header>')) {
        $failures[] = '(3) 관리자 대시보드 응답이 스킨 Layout의 header를 포함해야 한다.';
    }
    if (!str_contains($adminBody, '<footer>')) {
        $failures[] = '(3) 관리자 대시보드 응답이 스킨 Layout의 footer를 포함해야 한다.';
    }
    if (!str_contains($adminBody, 'class="site-sidebar"')) {
        $failures[] = '(3) 관리자 대시보드 응답이 스킨 Layout의 사이드바를 포함해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(3) in-process 테스트 실패: ' . $e->getMessage();
}

// (4) $accountRepository가 없으면(DB 미설정) GET /admin은 항상 /login으로 302해야 한다.
try {
    $_SESSION = [SessionUserResolver::SESSION_KEY => 'irrelevant-account-id'];
    $unconfiguredRouter = new Router();
    mintwiki_register_admin_route($unconfiguredRouter, null, new PhpSessionAdapter(), new AclService());

    $unconfiguredResponse = $unconfiguredRouter->match(new Request('GET', '/admin'))();
    if ($unconfiguredResponse->status() !== 302 || ($unconfiguredResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(4) DB 미설정 상태의 GET /admin은 /login으로 302여야 하는데 status=' . $unconfiguredResponse->status()
            . ', Location=' . ($unconfiguredResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(4) DB 미설정 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /admin route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /admin route 테스트 통과.\n");
exit(0);
