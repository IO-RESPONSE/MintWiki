<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\NavigationItem의 활성 상태 판단과 권한 요구를 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\NavigationItem;

$failures = [];

// id가 null인 경우 isActive는 항상 false를 반환해야 한다.
$itemWithoutId = new NavigationItem('/admin', '관리');
if ($itemWithoutId->isActive('/admin') !== false) {
    $failures[] = 'id가 null이면 isActive는 false를 반환해야 한다.';
}

// id와 currentPath가 정확히 일치할 때만 true를 반환해야 한다.
$itemWithId = new NavigationItem('/admin/status', '시스템 상태', '/admin/status');
if ($itemWithId->isActive('/admin/status') !== true) {
    $failures[] = 'id와 currentPath가 일치하면 isActive는 true를 반환해야 한다.';
}

// 부분 매치가 아닌 정확한 매치만 해야 한다.
if ($itemWithId->isActive('/admin') !== false) {
    $failures[] = '부분 매치는 활성으로 간주하면 안 된다.';
}

if ($itemWithId->isActive('/admin/status/details') !== false) {
    $failures[] = 'currentPath가 더 길면 활성으로 간주하면 안 된다.';
}

// requiresPermission 확인
$itemWithoutPermission = new NavigationItem('/public', '공개');
if ($itemWithoutPermission->requiresPermission() !== false) {
    $failures[] = 'requiredPermission이 null이면 requiresPermission은 false를 반환해야 한다.';
}

$itemWithPermission = new NavigationItem('/admin', '관리', null, 'admin:read');
if ($itemWithPermission->requiresPermission() !== true) {
    $failures[] = 'requiredPermission이 설정되면 requiresPermission은 true를 반환해야 한다.';
}

// 속성들을 제대로 반환하는지 확인
$item = new NavigationItem(
    '/admin/audit',
    '감사 로그',
    '/admin/audit',
    'audit:view'
);

if ($item->href() !== '/admin/audit') {
    $failures[] = 'href()가 정확한 값을 반환하지 않는다.';
}

if ($item->label() !== '감사 로그') {
    $failures[] = 'label()이 정확한 값을 반환하지 않는다.';
}

if ($item->id() !== '/admin/audit') {
    $failures[] = 'id()가 정확한 값을 반환하지 않는다.';
}

if ($item->requiredPermission() !== 'audit:view') {
    $failures[] = 'requiredPermission()이 정확한 값을 반환하지 않는다.';
}

if ($failures !== []) {
    fwrite(STDERR, "NavigationItem 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "NavigationItem 테스트 통과.\n");
exit(0);
