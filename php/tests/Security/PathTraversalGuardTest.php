<?php

declare(strict_types=1);

/**
 * MintWiki\Security\PathTraversalGuard의 경로 순회 차단을 확인한다.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\PathTraversalGuard;

$failures = [];
$guard = new PathTraversalGuard();

if ($guard->join('/home/account/wiki/storage/', 'cache/page.html') !== '/home/account/wiki/storage/cache/page.html') {
    $failures[] = '안전한 상대 경로를 storage 기준 경로 아래로 결합해야 한다.';
}

if ($guard->join('/home/account/wiki/storage', 'cache//page.html') !== '/home/account/wiki/storage/cache/page.html') {
    $failures[] = '중복 구분자는 안전한 경로 구간만 남기고 정규화해야 한다.';
}

if ($guard->join('/home/account/wiki/storage', '') !== '/home/account/wiki/storage') {
    $failures[] = '빈 상대 경로는 기준 경로 자체로 정규화해야 한다.';
}

$blockedPaths = [
    '../config/local-config.php',
    'cache/../../config/local-config.php',
    './cache/page.html',
    '/etc/passwd',
    'C:\\Windows\\win.ini',
    'C:Windows\\win.ini',
    '\\\\server\\share\\secret.txt',
    "cache/\0secret.txt",
];

foreach ($blockedPaths as $path) {
    try {
        $guard->join('/home/account/wiki/storage', $path);
        $failures[] = "위험한 경로를 차단해야 한다: {$path}";
    } catch (InvalidArgumentException) {
        // 기대한 차단 경로다.
    }
}

try {
    $guard->join('', 'cache/page.html');
    $failures[] = '빈 기준 경로를 차단해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 차단 경로다.
}

if ($failures !== []) {
    fwrite(STDERR, "PathTraversalGuard 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PathTraversalGuard 테스트 통과.\n");
exit(0);
