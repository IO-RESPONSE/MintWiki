<?php

declare(strict_types=1);

/**
 * MintWiki\Security\BackupDownloadGuard의 관리자 권한 및 경로 차단을 확인한다.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\BackupDownloadGuard;

$failures = [];
$guard = new BackupDownloadGuard();

$adminPermissions = ['document:view', 'admin:read'];
$safePath = $guard->guardedPath('/home/account/wiki/backups/', 'daily/site.sql', $adminPermissions);

if ($safePath !== '/home/account/wiki/backups/daily/site.sql') {
    $failures[] = '관리자 권한이 있으면 안전한 백업 상대 경로를 기준 경로 아래로 결합해야 한다.';
}

try {
    $guard->guardedPath('/home/account/wiki/backups', 'daily/site.sql', ['document:view']);
    $failures[] = '관리자 권한이 없으면 백업 다운로드 경로를 반환하면 안 된다.';
} catch (RuntimeException) {
    // 기대한 권한 차단이다.
}

try {
    $guard->guardedPath('/home/account/wiki/backups', '../config/local-config.php', $adminPermissions);
    $failures[] = '관리자 권한이 있어도 경로 순회 요청은 차단해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 경로 차단이다.
}

try {
    $guard->guardedPath('/home/account/wiki/backups', '/etc/passwd', $adminPermissions);
    $failures[] = '관리자 권한이 있어도 절대 경로 요청은 차단해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 경로 차단이다.
}

if (BackupDownloadGuard::REQUIRED_PERMISSION !== 'admin:read') {
    $failures[] = '백업 다운로드 guard는 admin:read 권한을 요구해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "BackupDownloadGuard 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "BackupDownloadGuard 테스트 통과.\n");
exit(0);
