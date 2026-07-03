<?php

declare(strict_types=1);

/**
 * MintWiki\App\StoragePathConfig의 저장소 경로 계산 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;
use MintWiki\App\StoragePathConfig;

$failures = [];

// 기본 storage 경로에서 하위 디렉터리를 계산한다.
$default = new StoragePathConfig(new ConfigLoader([]), '/var/www/wiki/storage/');
if ($default->rootPath() !== '/var/www/wiki/storage') {
    $failures[] = '기본 storage 경로의 마지막 슬래시를 제거해야 한다.';
}
if ($default->cachePath() !== '/var/www/wiki/storage/cache') {
    $failures[] = '기본 storage 경로에서 cache 경로를 계산해야 한다.';
}
if ($default->uploadsPath() !== '/var/www/wiki/storage/uploads') {
    $failures[] = '기본 storage 경로에서 uploads 경로를 계산해야 한다.';
}
if ($default->logsPath() !== '/var/www/wiki/storage/logs') {
    $failures[] = '기본 storage 경로에서 logs 경로를 계산해야 한다.';
}

// 파일 설정 값은 기본 경로를 덮어쓴다.
$fileConfigured = new StoragePathConfig(
    new ConfigLoader(['storage_path' => '/home/account/private/wiki-storage/']),
    '/var/www/wiki/storage'
);
if ($fileConfigured->rootPath() !== '/home/account/private/wiki-storage') {
    $failures[] = 'file-value의 storage_path가 기본 경로보다 우선해야 한다.';
}

// 환경변수는 파일 설정 값보다 우선한다.
putenv('WIKI_STORAGE_PATH=/srv/shared-hosting/storage/');
$envConfigured = new StoragePathConfig(
    new ConfigLoader(['storage_path' => '/home/account/private/wiki-storage']),
    '/var/www/wiki/storage'
);
if ($envConfigured->rootPath() !== '/srv/shared-hosting/storage') {
    $failures[] = 'WIKI_STORAGE_PATH 환경변수가 file-value보다 우선해야 한다.';
}
putenv('WIKI_STORAGE_PATH');

// 빈 문자열 설정은 실수로 루트 경로를 만들지 않고 기본값으로 되돌린다.
$emptyConfigured = new StoragePathConfig(
    new ConfigLoader(['storage_path' => '']),
    '/var/www/wiki/storage'
);
if ($emptyConfigured->rootPath() !== '/var/www/wiki/storage') {
    $failures[] = '빈 storage_path는 기본 경로로 대체해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "StoragePathConfig 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "StoragePathConfig 테스트 통과.\n");
exit(0);
