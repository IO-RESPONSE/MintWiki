<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Response::html() HTML 응답 helper의 기본 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0417 JsonResponseTest.php와
 * 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Response;

$failures = [];

$default = Response::html('<p>hi</p>');
if ($default->status() !== 200) {
    $failures[] = '기본 status는 200이어야 한다.';
}
$expectedHeaders = [
    'Content-Type' => 'text/html; charset=utf-8',
    'Cache-Control' => 'no-cache, no-store, must-revalidate',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
];
if ($default->headers() !== $expectedHeaders) {
    $failures[] = 'Content-Type, X-Content-Type-Options, X-Frame-Options, Content-Security-Policy 헤더가 올바르게 설정되어야 한다.';
}
if ($default->body() !== '<p>hi</p>') {
    $failures[] = 'body는 전달한 HTML 문자열을 그대로 담아야 한다.';
}

$withStatusAndHeaders = Response::html('<p>not found</p>', 404, ['X-Request-Id' => 'abc']);
if ($withStatusAndHeaders->status() !== 404) {
    $failures[] = 'status()가 전달한 값을 반환하지 않았다.';
}
$expectedHeadersWithExtra = [
    'Content-Type' => 'text/html; charset=utf-8',
    'Cache-Control' => 'no-cache, no-store, must-revalidate',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
    'X-Request-Id' => 'abc',
];
if ($withStatusAndHeaders->headers() !== $expectedHeadersWithExtra) {
    $failures[] = '추가 헤더가 보안 헤더와 함께 병합되어야 한다.';
}
if ($withStatusAndHeaders->body() !== '<p>not found</p>') {
    $failures[] = 'body()가 전달한 HTML 문자열을 반환하지 않았다.';
}

$empty = Response::html('');
if ($empty->body() !== '') {
    $failures[] = '빈 문자열도 그대로 body에 담겨야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Response::html() 헬퍼 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Response::html() 헬퍼 테스트 통과.\n");
exit(0);
