<?php

declare(strict_types=1);

/**
 * `MintWiki\Acl\PdoRepository::grantNamespacePermission()`(태스크 0696, 최초
 * 관리자 권한 부여용)의 동작을 확인하는 smoke test. phpunit 없이 `php`
 * CLI만으로 실행된다. 실제 DB 없이 sqlite in-memory에
 * `db/schema/acl_namespace_rule.sql`을 적용해 검증한다.
 *
 * 검증 대상:
 * (1) 규칙을 부여하면 `acl_namespace_rule`에 정확한 값으로 행이 하나 생긴다.
 * (2) 같은 namespace/subject_type/subject_id/permission으로 다시 부여를
 *     시도하면 중복 삽입되지 않는다(행 개수 그대로).
 * (3) 부여한 규칙은 `namespaceRules()`로 조회되고, `AclService::check()`가
 *     해당 subject에게 그 permission을 허용으로 판정한다.
 * (4) subject_id가 다르거나 permission이 다르면 별개의 규칙으로 추가된다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\Effect;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository;
use MintWiki\Acl\Permission;
use MintWiki\Acl\SubjectType;

$failures = [];
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../../db/schema/acl_namespace_rule.sql');
if ($aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/acl_namespace_rule.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec($aclNamespaceRuleSql);

$repository = new PdoRepository($connection);

// (1) 규칙을 부여하면 정확한 값으로 행이 하나 생긴다.
$repository->grantNamespacePermission(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    SubjectType::User,
    Permission::Admin,
    Effect::Allow,
    'admin-account-id'
);

$rows = $connection->query('SELECT * FROM acl_namespace_rule')->fetchAll(PDO::FETCH_ASSOC);
if (count($rows) !== 1) {
    $failures[] = '(1) 규칙 부여 후 acl_namespace_rule에 행이 정확히 1개 있어야 하는데 ' . count($rows) . '개였다.';
} else {
    $row = $rows[0];
    if ($row['namespace'] !== '*') {
        $failures[] = '(1) 부여된 규칙의 namespace는 "*"여야 한다.';
    }
    if ($row['subject_type'] !== 'user') {
        $failures[] = '(1) 부여된 규칙의 subject_type은 user여야 한다.';
    }
    if ($row['subject_id'] !== 'admin-account-id') {
        $failures[] = '(1) 부여된 규칙의 subject_id는 admin-account-id여야 한다.';
    }
    if ($row['permission'] !== 'admin') {
        $failures[] = '(1) 부여된 규칙의 permission은 admin이어야 한다.';
    }
    if ($row['effect'] !== 'allow') {
        $failures[] = '(1) 부여된 규칙의 effect는 allow여야 한다.';
    }
    if ($row['id'] === null || $row['id'] === '') {
        $failures[] = '(1) 부여된 규칙은 비어있지 않은 id를 가져야 한다.';
    }
}

// (2) 같은 조합으로 다시 부여해도 중복 삽입되지 않는다.
$repository->grantNamespacePermission(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    SubjectType::User,
    Permission::Admin,
    Effect::Allow,
    'admin-account-id'
);
$repository->grantNamespacePermission(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    SubjectType::User,
    Permission::Admin,
    Effect::Allow,
    'admin-account-id'
);

$rowsAfterRepeat = $connection->query('SELECT * FROM acl_namespace_rule')->fetchAll(PDO::FETCH_ASSOC);
if (count($rowsAfterRepeat) !== 1) {
    $failures[] = '(2) 같은 규칙을 반복 부여해도 행 개수는 1개 그대로여야 하는데 ' . count($rowsAfterRepeat) . '개였다.';
}

// (3) 부여한 규칙이 namespaceRules()로 조회되고, AclService가 허용으로 판정한다.
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    $repository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE)
);
$aclService = new AclService($namespaceAclDefaults);

$decision = $aclService->check(Permission::Admin, SubjectType::User, 'admin-account-id');
if (!$decision->isAllowed()) {
    $failures[] = '(3) 부여된 계정은 Permission::Admin 검사에서 허용되어야 한다.';
}

$otherUserDecision = $aclService->check(Permission::Admin, SubjectType::User, 'someone-else');
if ($otherUserDecision->isAllowed()) {
    $failures[] = '(3) 규칙이 없는 다른 사용자는 Permission::Admin이 허용되면 안 된다.';
}

// (4) subject_id가 다르면 별개의 규칙으로 추가된다.
$repository->grantNamespacePermission(
    NamespaceAclDefaults::DEFAULT_NAMESPACE,
    SubjectType::User,
    Permission::Admin,
    Effect::Allow,
    'another-admin-account-id'
);
$rowsAfterAnotherSubject = $connection->query('SELECT * FROM acl_namespace_rule')->fetchAll(PDO::FETCH_ASSOC);
if (count($rowsAfterAnotherSubject) !== 2) {
    $failures[] = '(4) 다른 subject_id로 부여하면 행이 추가되어야 하는데 총 ' . count($rowsAfterAnotherSubject) . '개였다.';
}

if ($failures !== []) {
    fwrite(STDERR, "PdoRepository::grantNamespacePermission() 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PdoRepository::grantNamespacePermission() 테스트 통과.\n");
exit(0);
