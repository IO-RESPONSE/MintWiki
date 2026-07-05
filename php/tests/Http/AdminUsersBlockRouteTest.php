<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0699에서 등록하는 `GET /admin/users/block`과
 * `POST /admin/users/block` route의 동작을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다(0698 AdminAuditRouteTest.php와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직을 Router에
 * 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 두 route 모두 인가 3경로(익명 302 /login, 비관리자 403, 관리자 통과)를
 *     따른다.
 * (2) 관리자의 GET /admin/users/block은 200으로 BlockUserFormPage(CSRF
 *     토큰 hidden 필드 포함)를 받는다.
 * (3) 관리자의 POST /admin/users/block은 CSRF 토큰이 없거나 유효하지 않으면
 *     403으로 거부하고 계정을 차단하지 않는다.
 * (4) 유효성 오류(빈 user_id/존재하지 않는 user_id/빈 reason)는 422로 폼에
 *     오류를 다시 표시하고 계정을 차단하지 않는다.
 * (5) 유효한 제출은 대상 계정을 차단(`blocked_at` 설정)하고 폼으로 302
 *     리다이렉트한다.
 * (6) `$accountRepository`가 없으면(DB 미설정) 두 route 모두 항상 `/login`
 *     으로 302한다(0674 계약과 동일).
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
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\BlockUserFormPage;
use MintWiki\Ui\Layout;
use MintWiki\User\AccountRepository;
use MintWiki\User\BlockUserHandler;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET /admin/users/block`과
 * `POST /admin/users/block` 핸들러와 동일한 등록 로직을 재구성한다(위 파일
 * docblock 참고).
 */
function mintwiki_register_admin_users_block_routes(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService
): void {
    $router->register('GET', '/admin/users/block', static function () use ($accountRepository, $sessionAdapter, $aclService): Response {
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

        $blockUserFormPage = new BlockUserFormPage(null, $layout);

        return Response::html($blockUserFormPage->render());
    });

    $router->register('POST', '/admin/users/block', static function () use ($accountRepository, $sessionAdapter, $aclService): Response {
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

        $blockUserFormPage = new BlockUserFormPage(null, $layout);
        $blockUserHandler = new BlockUserHandler($accountRepository, new CsrfTokenService(), $blockUserFormPage);

        return $blockUserHandler->handle($_POST);
    });
}

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
if ($accountSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/account.sql 또는 acl_namespace_rule.sql을 읽을 수 없습니다.\n");
    exit(1);
}

function mintwiki_admin_users_block_test_blocked_at(PDO $pdo, string $id): ?string
{
    $statement = $pdo->prepare('SELECT blocked_at FROM account WHERE id = :id');
    $statement->execute(['id' => $id]);
    $value = $statement->fetchColumn();

    return $value === false ? null : $value;
}

try {
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);
    $pdo->exec($aclNamespaceRuleSql);

    $accountRepository = new AccountRepository($pdo);
    $adminId = $accountRepository->create('admin', password_hash('irrelevant', PASSWORD_DEFAULT));
    $regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));
    $targetId = $accountRepository->create('target', password_hash('irrelevant', PASSWORD_DEFAULT));

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
    mintwiki_register_admin_users_block_routes($router, $accountRepository, $sessionAdapter, $aclService);

    // ------------------------------------------------------------------
    // (1) 인가 3경로 — GET /admin/users/block
    // ------------------------------------------------------------------
    $_SESSION = [];
    $anonGetResponse = $router->match(new Request('GET', '/admin/users/block'))();
    if ($anonGetResponse->status() !== 302 || ($anonGetResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(1) 비로그인 사용자의 GET /admin/users/block은 /login으로 302여야 하는데 status=' . $anonGetResponse->status()
            . ', Location=' . ($anonGetResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    $_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
    $regularGetResponse = $router->match(new Request('GET', '/admin/users/block'))();
    if ($regularGetResponse->status() !== 403) {
        $failures[] = '(1) 비관리자 사용자의 GET /admin/users/block은 403이어야 하는데 ' . $regularGetResponse->status() . '이었다.';
    }
    if (!str_contains($regularGetResponse->body(), '권한 없음')) {
        $failures[] = '(1) 비관리자 거부 응답은 PermissionDeniedPage를 보여줘야 한다.';
    }

    $_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
    $adminGetResponse = $router->match(new Request('GET', '/admin/users/block'))();
    if ($adminGetResponse->status() !== 200) {
        $failures[] = '(2) 관리자의 GET /admin/users/block은 200이어야 하는데 ' . $adminGetResponse->status() . '이었다.';
    }
    $adminGetBody = $adminGetResponse->body();
    if (!str_contains($adminGetBody, '<form method="post" action="/admin/users/block">')) {
        $failures[] = '(2) 사용자 차단 폼이 /admin/users/block으로 제출되어야 한다.';
    }
    if (!str_contains($adminGetBody, '<input type="hidden" name="csrf_token"')) {
        $failures[] = '(2) 사용자 차단 폼이 CSRF 토큰 hidden 필드를 포함해야 한다.';
    }
    if (!str_contains($adminGetBody, '<!doctype html>') || !str_contains($adminGetBody, '<header>') || !str_contains($adminGetBody, '<footer>')) {
        $failures[] = '(2) 사용자 차단 폼 응답이 스킨 Layout으로 렌더링되어야 한다.';
    }

    // ------------------------------------------------------------------
    // (1) 인가 3경로 — POST /admin/users/block
    // ------------------------------------------------------------------
    $_SESSION = [];
    $_POST = ['user_id' => $targetId, 'reason' => '스팸'];
    $anonPostResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($anonPostResponse->status() !== 302 || ($anonPostResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(1) 비로그인 사용자의 POST /admin/users/block은 /login으로 302여야 하는데 status=' . $anonPostResponse->status()
            . ', Location=' . ($anonPostResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    $_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
    $regularPostResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($regularPostResponse->status() !== 403) {
        $failures[] = '(1) 비관리자 사용자의 POST /admin/users/block은 403이어야 하는데 ' . $regularPostResponse->status() . '이었다.';
    }

    if (mintwiki_admin_users_block_test_blocked_at($pdo, $targetId) !== null) {
        $failures[] = '(1) 인가되지 않은 POST 시도로 계정이 차단되면 안 된다.';
    }

    // ------------------------------------------------------------------
    // (3) CSRF 누락/불일치 거부 — 관리자 세션.
    // ------------------------------------------------------------------
    $_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];

    $_POST = ['user_id' => $targetId, 'reason' => '스팸'];
    $missingCsrfResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($missingCsrfResponse->status() !== 403) {
        $failures[] = '(3) CSRF 토큰이 없는 제출은 403이어야 하는데 ' . $missingCsrfResponse->status() . '이었다.';
    }
    if (!str_contains($missingCsrfResponse->body(), '<form method="post" action="/admin/users/block">')) {
        $failures[] = '(3) CSRF 토큰이 없으면 사용자 차단 폼으로 되돌아가야 한다.';
    }

    $_POST = ['csrf_token' => 'not-a-real-token', 'user_id' => $targetId, 'reason' => '스팸'];
    $mismatchCsrfResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($mismatchCsrfResponse->status() !== 403) {
        $failures[] = '(3) 유효하지 않은 CSRF 토큰 제출은 403이어야 하는데 ' . $mismatchCsrfResponse->status() . '이었다.';
    }

    if (mintwiki_admin_users_block_test_blocked_at($pdo, $targetId) !== null) {
        $failures[] = '(3) CSRF 검증 실패 시 계정이 차단되면 안 된다.';
    }

    // ------------------------------------------------------------------
    // (4) 유효성 오류 재표시 — 빈 user_id.
    // ------------------------------------------------------------------
    $csrfService = new CsrfTokenService();
    $token = $csrfService->generate();
    $_POST = ['csrf_token' => $token, 'user_id' => '', 'reason' => '스팸'];
    $emptyUserIdResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($emptyUserIdResponse->status() !== 422) {
        $failures[] = '(4) 빈 user_id 제출은 422여야 하는데 ' . $emptyUserIdResponse->status() . '이었다.';
    }
    if (!str_contains($emptyUserIdResponse->body(), '사용자 ID를 입력하세요.')) {
        $failures[] = '(4) 빈 user_id 제출은 안내 오류 메시지를 표시해야 한다.';
    }

    // 존재하지 않는 user_id.
    $token = $csrfService->generate();
    $_POST = ['csrf_token' => $token, 'user_id' => 'no-such-account', 'reason' => '스팸'];
    $unknownUserIdResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($unknownUserIdResponse->status() !== 422) {
        $failures[] = '(4) 존재하지 않는 user_id 제출은 422여야 하는데 ' . $unknownUserIdResponse->status() . '이었다.';
    }
    if (!str_contains($unknownUserIdResponse->body(), '사용자를 찾을 수 없습니다.')) {
        $failures[] = '(4) 존재하지 않는 user_id 제출은 "사용자를 찾을 수 없습니다." 오류를 표시해야 한다.';
    }

    // 빈 reason.
    $token = $csrfService->generate();
    $_POST = ['csrf_token' => $token, 'user_id' => $targetId, 'reason' => ''];
    $emptyReasonResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($emptyReasonResponse->status() !== 422) {
        $failures[] = '(4) 빈 reason 제출은 422여야 하는데 ' . $emptyReasonResponse->status() . '이었다.';
    }
    if (!str_contains($emptyReasonResponse->body(), '차단 사유는 필수입니다.')) {
        $failures[] = '(4) 빈 reason 제출은 "차단 사유는 필수입니다." 오류를 표시해야 한다.';
    }

    if (mintwiki_admin_users_block_test_blocked_at($pdo, $targetId) !== null) {
        $failures[] = '(4) 유효성 검증 실패 시 계정이 차단되면 안 된다.';
    }

    // ------------------------------------------------------------------
    // (5) 유효한 제출 — 차단 후 302 리다이렉트.
    // ------------------------------------------------------------------
    $token = $csrfService->generate();
    $_POST = ['csrf_token' => $token, 'user_id' => $targetId, 'reason' => '스팸'];
    $successResponse = $router->match(new Request('POST', '/admin/users/block'))();
    if ($successResponse->status() !== 302 || ($successResponse->headers()['Location'] ?? null) !== '/admin/users/block') {
        $failures[] = '(5) 정상 제출은 /admin/users/block으로 302여야 하는데 status=' . $successResponse->status()
            . ', Location=' . ($successResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    if (mintwiki_admin_users_block_test_blocked_at($pdo, $targetId) === null) {
        $failures[] = '(5) 정상 제출 후 대상 계정의 blocked_at이 설정되어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(5) in-process 테스트 실패: ' . $e->getMessage();
}

// ------------------------------------------------------------------
// (6) $accountRepository가 없으면(DB 미설정) 두 route 모두 /login으로 302.
// ------------------------------------------------------------------
try {
    $_SESSION = [SessionUserResolver::SESSION_KEY => 'irrelevant-account-id'];
    $unconfiguredRouter = new Router();
    mintwiki_register_admin_users_block_routes($unconfiguredRouter, null, new PhpSessionAdapter(), new AclService());

    $unconfiguredGetResponse = $unconfiguredRouter->match(new Request('GET', '/admin/users/block'))();
    if ($unconfiguredGetResponse->status() !== 302 || ($unconfiguredGetResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(6) DB 미설정 상태의 GET /admin/users/block은 /login으로 302여야 하는데 status=' . $unconfiguredGetResponse->status()
            . ', Location=' . ($unconfiguredGetResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }

    $_POST = ['user_id' => 'irrelevant', 'reason' => '스팸'];
    $unconfiguredPostResponse = $unconfiguredRouter->match(new Request('POST', '/admin/users/block'))();
    if ($unconfiguredPostResponse->status() !== 302 || ($unconfiguredPostResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(6) DB 미설정 상태의 POST /admin/users/block은 /login으로 302여야 하는데 status=' . $unconfiguredPostResponse->status()
            . ', Location=' . ($unconfiguredPostResponse->headers()['Location'] ?? '(none)') . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(6) DB 미설정 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /admin/users/block route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /admin/users/block route 테스트 통과.\n");
exit(0);
