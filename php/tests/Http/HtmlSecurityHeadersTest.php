<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Response::html()에 추가된 보안 헤더(태스크 0554)의 동작을
 * 확인하는 테스트. phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Response;

$failures = [];

// 테스트 1: 기본 보안 헤더가 모두 포함되는지 확인
$response = Response::html('<p>test</p>');
$headers = $response->headers();

if (!isset($headers['X-Content-Type-Options']) || $headers['X-Content-Type-Options'] !== 'nosniff') {
    $failures[] = 'X-Content-Type-Options: nosniff 헤더가 포함되어야 한다.';
}

if (!isset($headers['X-Frame-Options']) || $headers['X-Frame-Options'] !== 'DENY') {
    $failures[] = 'X-Frame-Options: DENY 헤더가 포함되어야 한다.';
}

if (!isset($headers['Content-Security-Policy']) || $headers['Content-Security-Policy'] !== "default-src 'self'") {
    $failures[] = "Content-Security-Policy: default-src 'self' 헤더가 포함되어야 한다.";
}

// 테스트 2: 기본 Content-Type 헤더도 여전히 있는지 확인
if (!isset($headers['Content-Type']) || $headers['Content-Type'] !== 'text/html; charset=utf-8') {
    $failures[] = 'Content-Type: text/html; charset=utf-8 헤더가 포함되어야 한다.';
}

// 테스트 3: 추가 헤더가 보안 헤더를 덮어쓸 수 없는지 확인
// (기본값 + headers 병합에서 $defaultHeaders + $headers이므로 기본값이 우선)
$response = Response::html('<p>test</p>', 200, ['X-Content-Type-Options' => 'override']);
if ($response->headers()['X-Content-Type-Options'] === 'override') {
    $failures[] = '추가 헤더로 보안 헤더를 덮어쓸 수 없어야 한다 (기본값이 우선).';
}

// 테스트 4: 다른 추가 헤더는 병합되는지 확인
$response = Response::html('<p>test</p>', 200, ['X-Custom-Header' => 'custom-value']);
if (!isset($response->headers()['X-Custom-Header']) || $response->headers()['X-Custom-Header'] !== 'custom-value') {
    $failures[] = '다른 추가 헤더는 정상적으로 병합되어야 한다.';
}

// 테스트 5: 모든 보안 헤더가 status, body와 함께 정상 동작하는지 확인
$response = Response::html('<p>content</p>', 201, ['X-Id' => '123']);
if ($response->status() !== 201) {
    $failures[] = 'status가 정상적으로 설정되어야 한다.';
}
if ($response->body() !== '<p>content</p>') {
    $failures[] = 'body가 정상적으로 설정되어야 한다.';
}
if (!isset($response->headers()['X-Content-Type-Options'])) {
    $failures[] = 'status와 추가 헤더가 있어도 보안 헤더가 포함되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "HTML 응답 보안 헤더 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "HTML 응답 보안 헤더 테스트 통과.\n");
exit(0);
