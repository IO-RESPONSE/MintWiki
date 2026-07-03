<?php

declare(strict_types=1);

/**
 * UI ACL 연기 테스트(smoke test). ACL Decision의 거부 상태를 검증한다(태스크 0604).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 권한 검사 결과를 표현하는
 * Decision 클래스가 read/edit/admin 권한의 거부 상태를 올바르게 처리하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\Decision;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// (1) read 권한 거부 Decision 생성 및 상태 확인
$readDeniedDecision = new Decision('read', false, 'acl.no_matching_rule', null);
if ($readDeniedDecision->isDenied() !== true) {
    $failures[] = 'read 권한 거부 Decision은 isDenied()가 true여야 한다.';
}
if ($readDeniedDecision->isAllowed() !== false) {
    $failures[] = 'read 권한 거부 Decision은 isAllowed()가 false여야 한다.';
}
if ($readDeniedDecision->permission() !== 'read') {
    $failures[] = 'read 권한 Decision의 permission()은 "read"여야 한다.';
}
if ($readDeniedDecision->reason() !== 'acl.no_matching_rule') {
    $failures[] = 'read 권한 거부의 reason()은 "acl.no_matching_rule"이어야 한다.';
}

// (2) edit 권한 거부 Decision 생성 및 상태 확인
$editDeniedDecision = new Decision('edit', false, 'acl.matched_rule', 'rule-edit-denied');
if ($editDeniedDecision->isDenied() !== true) {
    $failures[] = 'edit 권한 거부 Decision은 isDenied()가 true여야 한다.';
}
if ($editDeniedDecision->isAllowed() !== false) {
    $failures[] = 'edit 권한 거부 Decision은 isAllowed()가 false여야 한다.';
}
if ($editDeniedDecision->permission() !== 'edit') {
    $failures[] = 'edit 권한 Decision의 permission()은 "edit"여야 한다.';
}
if ($editDeniedDecision->matchedRuleId() !== 'rule-edit-denied') {
    $failures[] = 'edit 권한 거부의 matchedRuleId()는 "rule-edit-denied"여야 한다.';
}

// (3) admin 권한 거부 Decision 생성 및 상태 확인
$adminDeniedDecision = new Decision('admin', false, 'acl.permission_denied', 'rule-admin-check');
if ($adminDeniedDecision->isDenied() !== true) {
    $failures[] = 'admin 권한 거부 Decision은 isDenied()가 true여야 한다.';
}
if ($adminDeniedDecision->isAllowed() !== false) {
    $failures[] = 'admin 권한 거부 Decision은 isAllowed()가 false여야 한다.';
}
if ($adminDeniedDecision->permission() !== 'admin') {
    $failures[] = 'admin 권한 Decision의 permission()은 "admin"이어야 한다.';
}

// (4) 허용 Decision도 올바르게 동작해야 한다
$allowedDecision = new Decision('read', true, 'acl.matched_rule', 'rule-read-allowed');
if ($allowedDecision->isAllowed() !== true) {
    $failures[] = 'read 권한 허용 Decision은 isAllowed()가 true여야 한다.';
}
if ($allowedDecision->isDenied() !== false) {
    $failures[] = 'read 권한 허용 Decision은 isDenied()가 false여야 한다.';
}

// (5) PermissionDeniedPage가 거부 Decision을 올바르게 렌더링할 수 있어야 한다
$escaper = new Escaper();
$layout = new Layout();
$deniedPage = new PermissionDeniedPage($escaper, $layout);

$html = $deniedPage->render($readDeniedDecision);
if (!str_contains($html, '권한 없음')) {
    $failures[] = 'PermissionDeniedPage 렌더링이 "권한 없음" 텍스트를 포함해야 한다.';
}
if (!str_contains($html, 'read')) {
    $failures[] = 'PermissionDeniedPage 렌더링이 "read" 권한 정보를 포함해야 한다.';
}
if (!str_contains($html, 'acl.no_matching_rule')) {
    $failures[] = 'PermissionDeniedPage 렌더링이 거부 이유를 포함해야 한다.';
}

// (6) edit 거부 Decision도 PermissionDeniedPage에서 올바르게 렌더링되어야 한다
$editDeniedHtml = $deniedPage->render($editDeniedDecision);
if (!str_contains($editDeniedHtml, 'edit')) {
    $failures[] = 'PermissionDeniedPage는 "edit" 권한 정보를 포함해야 한다.';
}
if (!str_contains($editDeniedHtml, 'acl.matched_rule')) {
    $failures[] = 'PermissionDeniedPage는 edit 거부의 reason을 포함해야 한다.';
}

// (7) admin 거부 Decision도 PermissionDeniedPage에서 올바르게 렌더링되어야 한다
$adminDeniedHtml = $deniedPage->render($adminDeniedDecision);
if (!str_contains($adminDeniedHtml, 'admin')) {
    $failures[] = 'PermissionDeniedPage는 "admin" 권한 정보를 포함해야 한다.';
}
if (!str_contains($adminDeniedHtml, 'acl.permission_denied')) {
    $failures[] = 'PermissionDeniedPage는 admin 거부의 reason을 포함해야 한다.';
}

// (8) 여러 Decision들이 서로 독립적이어야 한다 (상태 공유 없음)
$decision1 = new Decision('read', false, 'reason1');
$decision2 = new Decision('edit', true, 'reason2');
if ($decision1->permission() === $decision2->permission()) {
    $failures[] = '다른 Decision들의 권한이 서로 다르면 다르게 반환되어야 한다.';
}

// (9) matchedRuleId가 null일 수 있어야 한다
$decisionWithoutRuleId = new Decision('delete', false, 'acl.no_matching_rule');
if ($decisionWithoutRuleId->matchedRuleId() !== null) {
    $failures[] = 'matchedRuleId가 명시되지 않으면 null이어야 한다.';
}

// (10) 다양한 permission 문자열을 처리할 수 있어야 한다
$permissions = ['read', 'edit', 'admin', 'delete', 'move', 'discuss'];
foreach ($permissions as $perm) {
    $decision = new Decision($perm, false, 'test_reason');
    if ($decision->permission() !== $perm) {
        $failures[] = "'{$perm}' 권한이 올바르게 저장되어야 한다.";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "UI ACL 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI ACL 연기 테스트 통과.\n");
exit(0);
