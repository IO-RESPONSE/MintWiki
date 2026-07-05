<?php

declare(strict_types=1);

/**
 * `MintWiki\Security\AdminAccessGate`(태스크 0696)의 동작을 확인하는 smoke
 * test. phpunit 없이 `php` CLI만으로 실행된다. 실제 DB 없이 sqlite
 * in-memory에 `db/schema/account.sql`과 `db/schema/acl_namespace_rule.sql`을
 * 적용해 세 가지 인가 경로를 검증한다.
 *
 * 검증 대상:
 * (1) 비로그인(익명) 사용자는 authorize()가 `/login`으로 302 Response를 반환한다.
 * (2) 로그인했지만 관리자 권한(acl_namespace_rule의 admin allow 규칙)이 없는
 *     사용자는 403 Response(PermissionDeniedPage)를 반환한다.
 * (3) `acl_namespace_rule`에 admin allow 규칙이 있는 사용자는 authorize()가
 *     null을 반환해 라우팅이 계속될 수 있다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\Effect;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission;
use MintWiki\Acl\SubjectType;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\User\AccountRepository;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
if ($accountSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/account.sql 또는 db/schema/acl_namespace_rule.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec($accountSql);
$connection->exec($aclNamespaceRuleSql);

$accountRepository = new AccountRepository($connection);
$adminId = $accountRepository->create('admin', password_hash('irrelevant', PASSWORD_DEFAULT));
$regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));

$aclRepository = new AclPdoRepository($connection);
$aclRepository->grantNamespacePermission(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    SubjectType::User,
    Permission::Admin,
    Effect::Allow,
    $adminId
);

$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    $aclRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE)
);
$aclService = new AclService($namespaceAclDefaults);

$sessionAdapter = new PhpSessionAdapter();
$sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
$gate = new AdminAccessGate($aclService, $sessionUserResolver);

// (1) 비로그인(익명) → /login으로 302.
$_SESSION = [];
$anonResponse = $gate->authorize();
if ($anonResponse === null) {
    $failures[] = '(1) 비로그인 사용자는 authorize()가 Response를 반환해야 하는데 null이었다.';
} elseif ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(1) 비로그인 사용자는 /login으로 302여야 하는데 status=' . $anonResponse->status()
        . ', Location=' . ($anonResponse->headers()['Location'] ?? '(none)') . '이었다.';
}

// (2) 로그인했으나 관리자가 아님 → 403.
$_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
$regularResponse = $gate->authorize();
if ($regularResponse === null) {
    $failures[] = '(2) 비관리자 사용자는 authorize()가 Response를 반환해야 하는데 null이었다.';
} else {
    if ($regularResponse->status() !== 403) {
        $failures[] = '(2) 비관리자 사용자는 403이어야 하는데 ' . $regularResponse->status() . '이었다.';
    }
    if (!str_contains($regularResponse->body(), '권한 없음')) {
        $failures[] = '(2) 비관리자 거부 응답은 PermissionDeniedPage를 보여줘야 한다.';
    }
}

// (3) 관리자 → null(라우팅 계속).
$_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
$adminResponse = $gate->authorize();
if ($adminResponse !== null) {
    $failures[] = '(3) 관리자는 authorize()가 null을 반환해야 하는데 status=' . $adminResponse->status() . '을 반환했다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AdminAccessGate 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminAccessGate 테스트 통과.\n");
exit(0);
