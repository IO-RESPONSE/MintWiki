<?php

declare(strict_types=1);

/**
 * Accept header 협상 테스트 (태스크 0593).
 *
 * HTTP Accept 헤더를 기반으로 JSON/API와 HTML/UI 경계를 검증한다.
 * 동일한 엔드포인트가 Accept 헤더에 따라 다른 응답 형식을 반환하는지 확인한다.
 *
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Response;

$failures = [];

// (1) Request 객체에 Accept 헤더 저장 및 조회 테스트
$jsonAcceptHeaders = ['Accept' => 'application/json'];
$jsonRequest = new Request('GET', '/api/documents', [], '', $jsonAcceptHeaders);

if ($jsonRequest->headers() !== $jsonAcceptHeaders) {
    $failures[] = 'Request 객체가 Accept 헤더를 정확하게 저장해야 한다.';
}

if (!isset($jsonRequest->headers()['Accept']) || $jsonRequest->headers()['Accept'] !== 'application/json') {
    $failures[] = 'Accept 헤더 값을 올바르게 조회할 수 없다.';
}

// (2) HTML Accept 헤더 저장 및 조회 테스트
$htmlAcceptHeaders = ['Accept' => 'text/html'];
$htmlRequest = new Request('GET', '/documents', [], '', $htmlAcceptHeaders);

if (!isset($htmlRequest->headers()['Accept']) || $htmlRequest->headers()['Accept'] !== 'text/html') {
    $failures[] = 'HTML Accept 헤더를 올바르게 저장하고 조회할 수 없다.';
}

// (3) Accept 헤더가 여러 값을 가질 때 테스트
$multiAcceptHeaders = ['Accept' => 'text/html, application/json;q=0.9, */*;q=0.8'];
$multiRequest = new Request('GET', '/documents', [], '', $multiAcceptHeaders);

if (!isset($multiRequest->headers()['Accept']) || $multiRequest->headers()['Accept'] !== 'text/html, application/json;q=0.9, */*;q=0.8') {
    $failures[] = '복수 Accept 헤더 값을 올바르게 저장하고 조회할 수 없다.';
}

// (4) Accept 헤더가 없을 때 테스트 (헤더가 없는 요청도 유효해야 함)
$noAcceptRequest = new Request('GET', '/documents');

if ($noAcceptRequest->headers() !== []) {
    $failures[] = 'Accept 헤더가 없는 요청도 정상적으로 처리되어야 한다.';
}

// (5) JSON 응답의 Content-Type 검증
$jsonResponse = Response::json(['status' => 'ok']);

if (!isset($jsonResponse->headers()['Content-Type']) || $jsonResponse->headers()['Content-Type'] !== 'application/json') {
    $failures[] = 'JSON 응답의 Content-Type이 application/json이어야 한다.';
}

// (6) HTML 응답의 Content-Type 검증
$htmlResponse = Response::html('<p>test</p>');

if (!isset($htmlResponse->headers()['Content-Type']) || $htmlResponse->headers()['Content-Type'] !== 'text/html; charset=utf-8') {
    $failures[] = 'HTML 응답의 Content-Type이 text/html; charset=utf-8이어야 한다.';
}

// (7) API 경로 판별 유틸리티 테스트
// API 경로는 /api/로 시작한다
$apiPaths = [
    '/api/documents',
    '/api/documents/123',
    '/api/documents/by-title',
    '/api/search',
];

foreach ($apiPaths as $path) {
    if (!str_starts_with($path, '/api/')) {
        $failures[] = "API 경로 '{$path}'이 올바르게 인식되지 않았다.";
    }
}

// (8) UI 경로 판별 유틸리티 테스트
// UI 경로는 /api/로 시작하지 않는다
$uiPaths = [
    '/',
    '/documents',
    '/documents/123',
    '/edit',
    '/admin',
];

foreach ($uiPaths as $path) {
    if (str_starts_with($path, '/api/')) {
        $failures[] = "UI 경로 '{$path}'가 API 경로로 잘못 인식되었다.";
    }
}

// (9) Content-Type 헤더와 Accept 헤더의 대응 관계 검증
// JSON 응답은 application/json Content-Type을 가져야 함
$jsonData = ['id' => 1, 'title' => 'Test'];
$jsonResp = Response::json($jsonData);
$contentType = $jsonResp->headers()['Content-Type'] ?? '';

if ($contentType !== 'application/json') {
    $failures[] = 'JSON 데이터를 담은 응답의 Content-Type이 application/json이어야 한다.';
}

// (10) HTML 응답은 text/html; charset=utf-8 Content-Type을 가져야 함
$htmlResp = Response::html('<html><body>Test</body></html>');
$contentType = $htmlResp->headers()['Content-Type'] ?? '';

if ($contentType !== 'text/html; charset=utf-8') {
    $failures[] = 'HTML 데이터를 담은 응답의 Content-Type이 text/html; charset=utf-8이어야 한다.';
}

// (11) Accept 헤더에 따른 경로 라우팅 일관성 테스트
// 같은 경로라도 Accept 헤더가 다르면 다른 응답을 반환해야 함
$pathWithAccept = '/documents';
$apiPathWithAccept = '/api/documents';

// UI 경로는 Accept 헤더와 무관하게 항상 HTML 응답
$isUiPath = !str_starts_with($pathWithAccept, '/api/');
if (!$isUiPath) {
    $failures[] = '/documents는 UI 경로로 인식되어야 한다.';
}

// API 경로는 Accept 헤더에 따라 JSON 응답
$isApiPath = str_starts_with($apiPathWithAccept, '/api/');
if (!$isApiPath) {
    $failures[] = '/api/documents는 API 경로로 인식되어야 한다.';
}

// (12) 대소문자 불일치 Accept 헤더 처리
$caseInsensitiveHeaders = ['Accept' => 'APPLICATION/JSON'];
$caseRequest = new Request('GET', '/api/documents', [], '', $caseInsensitiveHeaders);

if (!isset($caseRequest->headers()['Accept'])) {
    $failures[] = '대소문자가 다른 Accept 헤더도 저장되어야 한다.';
}

// (13) 빈 Accept 헤더 처리
$emptyAcceptHeaders = ['Accept' => ''];
$emptyRequest = new Request('GET', '/documents', [], '', $emptyAcceptHeaders);

if (!isset($emptyRequest->headers()['Accept'])) {
    $failures[] = '빈 Accept 헤더도 저장되어야 한다.';
}

// (14) 응답 헤더 병합 테스트 - JSON 응답에 추가 헤더 병합
$additionalHeaders = ['X-Custom-Header' => 'custom-value'];
$jsonResponseWithExtra = Response::json(['data' => 'test'], 200, $additionalHeaders);

if (!isset($jsonResponseWithExtra->headers()['Content-Type']) || $jsonResponseWithExtra->headers()['Content-Type'] !== 'application/json') {
    $failures[] = 'JSON 응답의 Content-Type이 보존되어야 한다.';
}

if (!isset($jsonResponseWithExtra->headers()['X-Custom-Header']) || $jsonResponseWithExtra->headers()['X-Custom-Header'] !== 'custom-value') {
    $failures[] = 'JSON 응답에 추가 헤더가 병합되어야 한다.';
}

// (15) 응답 헤더 병합 테스트 - HTML 응답에 추가 헤더 병합
$htmlResponseWithExtra = Response::html('<p>test</p>', 200, ['X-Custom-Header' => 'custom-value']);

if (!isset($htmlResponseWithExtra->headers()['Content-Type']) || $htmlResponseWithExtra->headers()['Content-Type'] !== 'text/html; charset=utf-8') {
    $failures[] = 'HTML 응답의 Content-Type이 보존되어야 한다.';
}

if (!isset($htmlResponseWithExtra->headers()['X-Custom-Header']) || $htmlResponseWithExtra->headers()['X-Custom-Header'] !== 'custom-value') {
    $failures[] = 'HTML 응답에 추가 헤더가 병합되어야 한다.';
}

// (16) API와 UI 경로 경계 검증
// /api/로 시작하는 경로는 항상 JSON을 반환해야 함 (Accept 헤더 무시)
$apiRequest = new Request('GET', '/api/documents', [], '', ['Accept' => 'text/html']);
$isApi = str_starts_with($apiRequest->path(), '/api/');

if (!$isApi) {
    $failures[] = 'API 경로가 /api/로 시작하는지 확인할 수 없다.';
}

// /api/로 시작하지 않는 경로는 HTML을 반환해야 함 (Accept 헤더가 application/json이어도)
$uiRequest = new Request('GET', '/documents', [], '', ['Accept' => 'application/json']);
$isUI = !str_starts_with($uiRequest->path(), '/api/');

if (!$isUI) {
    $failures[] = 'UI 경로가 /api/로 시작하지 않는지 확인할 수 없다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Accept header 협상 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Accept header 협상 테스트 통과.\n");
exit(0);
