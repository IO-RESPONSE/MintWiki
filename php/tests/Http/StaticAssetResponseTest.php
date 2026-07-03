<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Response::staticAsset() 정적 자산 응답 helper의 기본 동작을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Response;

$failures = [];

// 기본: hash 없는 파일 (단순 파일명)
$noHash = Response::staticAsset('text/css', 'body { color: red; }', 'responsive-table.css');
if ($noHash->status() !== 200) {
    $failures[] = '기본 status는 200이어야 한다.';
}
$expectedHeadersNoHash = [
    'Content-Type' => 'text/css',
    'Cache-Control' => 'public, max-age=3600',
];
if ($noHash->headers() !== $expectedHeadersNoHash) {
    $failures[] = 'hash 없는 파일은 1시간 캐시 헤더를 가져야 한다. 실제: ' . json_encode($noHash->headers());
}
if ($noHash->body() !== 'body { color: red; }') {
    $failures[] = 'body는 전달한 내용을 그대로 담아야 한다.';
}

// hash가 있는 파일 (webpack 패턴)
$withHash = Response::staticAsset('application/javascript', 'console.log("hi");', 'app.abc123def456.js');
if ($withHash->status() !== 200) {
    $failures[] = 'hash가 있는 파일도 기본 status는 200이어야 한다.';
}
$expectedHeadersWithHash = [
    'Content-Type' => 'application/javascript',
    'Cache-Control' => 'public, max-age=31536000, immutable',
];
if ($withHash->headers() !== $expectedHeadersWithHash) {
    $failures[] = 'hash가 있는 파일은 1년 캐시 및 immutable 헤더를 가져야 한다. 실제: ' . json_encode($withHash->headers());
}
if ($withHash->body() !== 'console.log("hi");') {
    $failures[] = 'body는 전달한 내용을 그대로 담아야 한다.';
}

// 추가 헤더와 함께
$withExtra = Response::staticAsset('image/png', 'PNG_DATA', 'image.xyz789.png', 200, ['X-Custom' => 'value']);
$expectedHeadersWithExtra = [
    'Content-Type' => 'image/png',
    'Cache-Control' => 'public, max-age=31536000, immutable',
    'X-Custom' => 'value',
];
if ($withExtra->headers() !== $expectedHeadersWithExtra) {
    $failures[] = '추가 헤더가 기본 헤더와 함께 병합되어야 한다. 실제: ' . json_encode($withExtra->headers());
}

// 파일명이 비어있는 경우 (hash 없는 것으로 간주)
$emptyFilename = Response::staticAsset('text/css', 'body {}');
$expectedEmptyFilename = [
    'Content-Type' => 'text/css',
    'Cache-Control' => 'public, max-age=3600',
];
if ($emptyFilename->headers() !== $expectedEmptyFilename) {
    $failures[] = '파일명이 비어있을 때는 hash가 없는 것으로 간주해야 한다. 실제: ' . json_encode($emptyFilename->headers());
}

// hash가 너무 짧은 경우 (8자 미만)
$shortHash = Response::staticAsset('text/css', 'body {}', 'style.short.css');
$expectedShortHash = [
    'Content-Type' => 'text/css',
    'Cache-Control' => 'public, max-age=3600',
];
if ($shortHash->headers() !== $expectedShortHash) {
    $failures[] = 'hash가 8자 미만이면 hash가 없는 것으로 간주해야 한다. 실제: ' . json_encode($shortHash->headers());
}

// 상태 코드 변경
$notFound = Response::staticAsset('text/html', 'Not Found', 'error.html', 404);
if ($notFound->status() !== 404) {
    $failures[] = 'status()가 전달한 값을 반환하지 않았다.';
}

// 여러 점이 있는 복잡한 파일명
$complex = Response::staticAsset('text/css', 'body {}', 'vendor.bundle.abc123def456.min.css');
$expectedComplex = [
    'Content-Type' => 'text/css',
    'Cache-Control' => 'public, max-age=31536000, immutable',
];
if ($complex->headers() !== $expectedComplex) {
    $failures[] = '여러 점이 있는 파일명에서 hash를 정확히 감지해야 한다. 실제: ' . json_encode($complex->headers());
}

if ($failures !== []) {
    fwrite(STDERR, "Response::staticAsset() 헬퍼 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Response::staticAsset() 헬퍼 테스트 통과.\n");
exit(0);
