<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Response::json() JSON 응답 helper의 기본 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0395 ResponseTest.php와
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

$default = Response::json(['title' => 'hi']);
if ($default->status() !== 200) {
    $failures[] = '기본 status는 200이어야 한다.';
}
if ($default->headers() !== ['Content-Type' => 'application/json']) {
    $failures[] = 'Content-Type 헤더가 application/json으로 설정되어야 한다.';
}
if ($default->body() !== '{"title":"hi"}') {
    $failures[] = 'body는 데이터를 JSON으로 인코딩한 문자열이어야 한다.';
}

$withStatusAndHeaders = Response::json(['id' => 1], 201, ['X-Request-Id' => 'abc']);
if ($withStatusAndHeaders->status() !== 201) {
    $failures[] = 'status()가 전달한 값을 반환하지 않았다.';
}
if ($withStatusAndHeaders->headers() !== ['Content-Type' => 'application/json', 'X-Request-Id' => 'abc']) {
    $failures[] = '추가 헤더가 Content-Type과 함께 병합되어야 한다.';
}
if ($withStatusAndHeaders->body() !== '{"id":1}') {
    $failures[] = 'body()가 전달한 데이터를 JSON으로 인코딩하지 않았다.';
}

$emptyList = Response::json([]);
if ($emptyList->body() !== '[]') {
    $failures[] = '빈 배열은 JSON 배열([])로 인코딩되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Response::json() 헬퍼 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Response::json() 헬퍼 테스트 통과.\n");
exit(0);
