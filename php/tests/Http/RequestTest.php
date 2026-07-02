<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Request value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0395 ResponseTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;

$failures = [];

$default = new Request('GET', '/');
if ($default->method() !== 'GET') {
    $failures[] = '기본 생성자는 지정한 method를 그대로 반환해야 한다.';
}
if ($default->path() !== '/') {
    $failures[] = '기본 생성자는 지정한 path를 그대로 반환해야 한다.';
}
if ($default->query() !== []) {
    $failures[] = '기본 생성자는 빈 query 배열을 반환해야 한다.';
}
if ($default->body() !== '') {
    $failures[] = '기본 생성자는 빈 body 문자열을 반환해야 한다.';
}
if ($default->headers() !== []) {
    $failures[] = '기본 생성자는 빈 headers 배열을 반환해야 한다.';
}

$query = ['page' => '2'];
$headers = ['Content-Type' => 'application/json'];
$request = new Request('POST', '/articles', $query, '{"title":"hi"}', $headers);

if ($request->method() !== 'POST') {
    $failures[] = 'method()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($request->path() !== '/articles') {
    $failures[] = 'path()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($request->query() !== $query) {
    $failures[] = 'query()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($request->body() !== '{"title":"hi"}') {
    $failures[] = 'body()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($request->headers() !== $headers) {
    $failures[] = 'headers()가 생성자에 전달한 값을 반환하지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Request value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Request value object 테스트 통과.\n");
exit(0);
