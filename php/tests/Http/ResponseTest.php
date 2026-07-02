<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Response value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0393 AutoloadSmokeTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Response;

$failures = [];

$default = new Response(200);
if ($default->status() !== 200) {
    $failures[] = '기본 생성자는 지정한 status를 그대로 반환해야 한다.';
}
if ($default->headers() !== []) {
    $failures[] = '기본 생성자는 빈 headers 배열을 반환해야 한다.';
}
if ($default->body() !== '') {
    $failures[] = '기본 생성자는 빈 body 문자열을 반환해야 한다.';
}

$headers = ['Content-Type' => 'text/plain; charset=utf-8'];
$response = new Response(404, $headers, 'not found');

if ($response->status() !== 404) {
    $failures[] = 'status()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($response->headers() !== $headers) {
    $failures[] = 'headers()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($response->body() !== 'not found') {
    $failures[] = 'body()가 생성자에 전달한 값을 반환하지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Response value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Response value object 테스트 통과.\n");
exit(0);
