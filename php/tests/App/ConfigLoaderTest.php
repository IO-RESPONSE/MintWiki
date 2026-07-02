<?php

declare(strict_types=1);

/**
 * MintWiki\App\ConfigLoader의 계약을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다 (0414 Admin/ServiceTest.php와 동일한 방식).
 *
 * (1) `WIKI_` 접두어 환경변수가 설정되어 있으면 그 값을 우선 반환하는지,
 * (2) 환경변수가 없으면 생성자로 전달된 file-value 배열의 값을 반환하는지,
 * (3) 환경변수도 file-value도 없으면 호출자가 넘긴 `$default`를 반환하는지
 * 만 확인한다. `.env` 파일 자체를 읽는 로직은 이 태스크의 범위 밖이다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;

$failures = [];

// (1) 환경변수 우선.
putenv('WIKI_APP_NAME=env-value');
$loader = new ConfigLoader(['app_name' => 'file-value']);
if ($loader->get('app_name') !== 'env-value') {
    $failures[] = '환경변수 WIKI_APP_NAME이 설정되어 있으면 그 값을 우선 반환해야 한다.';
}
putenv('WIKI_APP_NAME');

// (2) 환경변수 없으면 file-value 배열 값.
$loader = new ConfigLoader(['app_name' => 'file-value']);
if ($loader->get('app_name') !== 'file-value') {
    $failures[] = '환경변수가 없으면 생성자로 전달된 file-value를 반환해야 한다.';
}

// (3) 둘 다 없으면 default.
$loader = new ConfigLoader([]);
if ($loader->get('missing_key', 'fallback') !== 'fallback') {
    $failures[] = '환경변수와 file-value가 모두 없으면 $default를 반환해야 한다.';
}

if ($loader->get('missing_key') !== null) {
    $failures[] = '$default를 생략하면 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ConfigLoader 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ConfigLoader 테스트 통과.\n");
exit(0);
