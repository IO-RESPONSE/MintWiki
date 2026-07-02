<?php

declare(strict_types=1);

/**
 * MintWiki\Acl\Decision value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0404 RevisionTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\Decision;

$failures = [];

$allowed = new Decision('read', true, 'acl.matched_rule', 'all-read-allow');

if ($allowed->permission() !== 'read') {
    $failures[] = 'permission()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($allowed->isAllowed() !== true) {
    $failures[] = 'isAllowed()가 true를 반환하지 않았다.';
}
if ($allowed->isDenied() !== false) {
    $failures[] = 'isDenied()가 isAllowed()의 반대값을 반환하지 않았다.';
}
if ($allowed->reason() !== 'acl.matched_rule') {
    $failures[] = 'reason()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($allowed->matchedRuleId() !== 'all-read-allow') {
    $failures[] = 'matchedRuleId()가 생성자에 전달한 값을 반환하지 않았다.';
}

$deniedWithMatchedRule = new Decision('delete', false, 'acl.matched_rule', 'all-delete-deny');

if ($deniedWithMatchedRule->isAllowed() !== false) {
    $failures[] = '거부 규칙이 일치하면 isAllowed()는 false여야 한다.';
}
if ($deniedWithMatchedRule->isDenied() !== true) {
    $failures[] = '거부 규칙이 일치하면 isDenied()는 true여야 한다.';
}
if ($deniedWithMatchedRule->reason() !== 'acl.matched_rule') {
    $failures[] = '규칙이 거부해서 막힌 경우에도 reason은 acl.matched_rule이어야 한다.';
}

$deniedWithNoMatch = new Decision('read', false, 'acl.no_matching_rule');

if ($deniedWithNoMatch->matchedRuleId() !== null) {
    $failures[] = 'matchedRuleId 기본값은 null이어야 한다.';
}
if ($deniedWithNoMatch->reason() !== 'acl.no_matching_rule') {
    $failures[] = '일치하는 규칙이 없으면 reason은 acl.no_matching_rule이어야 한다.';
}
if ($deniedWithNoMatch->isDenied() !== true) {
    $failures[] = '일치하는 규칙이 없으면 isDenied()는 true여야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Decision value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Decision value object 테스트 통과.\n");
exit(0);
