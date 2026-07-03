<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\Navigation의 활성 상태 판단과 권한 필터링을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationItem;

$failures = [];

// 빈 Navigation 생성
$emptyNav = new Navigation();
if (count($emptyNav->items()) !== 0) {
    $failures[] = 'Navigation은 빈 배열로 초기화될 수 있어야 한다.';
}

// 항목들을 포함한 Navigation 생성
$items = [
    new NavigationItem('/home', '홈', '/home'),
    new NavigationItem('/admin', '관리', '/admin', 'admin:read'),
    new NavigationItem('/audit', '감사', '/audit', 'audit:view'),
];
$nav = new Navigation($items);

if (count($nav->items()) !== 3) {
    $failures[] = 'items()가 정확한 개수를 반환하지 않는다.';
}

// findActive 확인
$activeItem = $nav->findActive('/home');
if ($activeItem === null || $activeItem->label() !== '홈') {
    $failures[] = 'findActive는 활성 항목을 정확히 찾아야 한다.';
}

if ($nav->findActive('/notfound') !== null) {
    $failures[] = 'findActive는 존재하지 않는 경로에 대해 null을 반환해야 한다.';
}

// filterByPermissions 확인 - 권한이 없는 사용자
$filtered = $nav->filterByPermissions([]);
if (count($filtered) !== 1 || $filtered[0]->label() !== '홈') {
    $failures[] = 'filterByPermissions는 권한을 요구하지 않는 항목만 반환해야 한다.';
}

// filterByPermissions 확인 - admin 권한만 있는 사용자
$filtered = $nav->filterByPermissions(['admin:read']);
if (count($filtered) !== 2) {
    $failures[] = 'filterByPermissions는 권한을 요구하지 않는 항목과 권한이 있는 항목을 반환해야 한다.';
}

// filterByPermissions 확인 - 모든 권한이 있는 사용자
$filtered = $nav->filterByPermissions(['admin:read', 'audit:view']);
if (count($filtered) !== 3) {
    $failures[] = 'filterByPermissions는 모든 항목을 반환해야 한다.';
}

// findActiveWithPermissions 확인 - 권한이 없어서 항목을 볼 수 없는 경우
$activeWithPerm = $nav->findActiveWithPermissions('/admin', []);
if ($activeWithPerm !== null) {
    $failures[] = 'findActiveWithPermissions는 권한이 없으면 항목을 반환하면 안 된다.';
}

// findActiveWithPermissions 확인 - 권한이 있어서 항목을 볼 수 있는 경우
$activeWithPerm = $nav->findActiveWithPermissions('/admin', ['admin:read']);
if ($activeWithPerm === null || $activeWithPerm->label() !== '관리') {
    $failures[] = 'findActiveWithPermissions는 권한이 있을 때 활성 항목을 반환해야 한다.';
}

// findActiveWithPermissions 확인 - 경로가 일치하지 않는 경우
$activeWithPerm = $nav->findActiveWithPermissions('/notfound', ['admin:read', 'audit:view']);
if ($activeWithPerm !== null) {
    $failures[] = 'findActiveWithPermissions는 경로가 일치하지 않으면 null을 반환해야 한다.';
}

// 항목 없이 초기화된 Navigation에서도 동작하는지 확인
$navWithoutIdItems = new Navigation([
    new NavigationItem('/public1', '공개1'),
    new NavigationItem('/public2', '공개2'),
]);
$noActiveItem = $navWithoutIdItems->findActive('/anything');
if ($noActiveItem !== null) {
    $failures[] = 'id 없는 항목들로만 이루어진 Navigation에서는 활성 항목이 없어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Navigation 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Navigation 테스트 통과.\n");
exit(0);
