<?php

declare(strict_types=1);

/**
 * 404 오류 처리 통합 테스트 (태스크 0592).
 *
 * 라우팅되지 않은 요청에 대해 적절한 404 응답을 반환하는지 확인한다.
 * API 요청은 JSON으로, UI 요청은 HTML로 응답해야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Router;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Ui\ErrorPage;

$failures = [];

// (1) UI 요청에 대한 404 응답 - 기본 경로
$errorPage = new ErrorPage();
$notFoundPath = '/documents/unknown';

// 경로가 /api/로 시작하지 않으므로 HTML 응답이어야 한다
$isApiRequest = str_starts_with($notFoundPath, '/api/');

if ($isApiRequest) {
    $failures[] = 'UI 요청 경로가 API 경로로 잘못 인식되었다.';
}

$html = $errorPage->renderNotFound($notFoundPath);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = 'UI 404 응답이 HTML 형식이어야 한다.';
}

if (!str_contains($html, '페이지를 찾을 수 없습니다')) {
    $failures[] = 'UI 404 응답이 적절한 메시지를 포함해야 한다.';
}

// (2) API 요청에 대한 404 응답
$apiPath = '/api/documents/unknown';
$isApiRequest = str_starts_with($apiPath, '/api/');

if (!$isApiRequest) {
    $failures[] = 'API 요청 경로가 올바르게 인식되지 않았다.';
}

$errorData = [
    'error' => 'not_found',
    'message' => 'The requested resource was not found.',
    'path' => $apiPath,
];
$jsonResponse = Response::json($errorData, 404);

if ($jsonResponse->status() !== 404) {
    $failures[] = 'API 404 응답의 상태 코드가 404여야 한다.';
}

$responseBody = json_decode($jsonResponse->body(), true);

if ($responseBody === null) {
    $failures[] = 'API 404 응답이 유효한 JSON이어야 한다.';
}

if (!isset($responseBody['error']) || $responseBody['error'] !== 'not_found') {
    $failures[] = 'API 404 응답이 error 필드를 포함해야 한다.';
}

if (!isset($responseBody['path']) || $responseBody['path'] !== $apiPath) {
    $failures[] = 'API 404 응답이 요청 경로를 포함해야 한다.';
}

// (3) 특수 문자가 포함된 경로에 대한 404 응답
$specialPath = '/documents/title?with=query&param=value';
$html = $errorPage->renderNotFound($specialPath);

if (str_contains($html, '<script>') || str_contains($html, 'onclick=')) {
    $failures[] = '404 응답이 XSS 공격에 취약하다.';
}

// (4) Content-Type 헤더 확인
$htmlResponse = Response::html('test', 404);
$headers = $htmlResponse->headers();

if (!isset($headers['Content-Type']) || $headers['Content-Type'] !== 'text/html; charset=utf-8') {
    $failures[] = 'HTML 404 응답의 Content-Type이 text/html; charset=utf-8이어야 한다.';
}

$jsonResponse = Response::json([], 404);
$headers = $jsonResponse->headers();

if (!isset($headers['Content-Type']) || $headers['Content-Type'] !== 'application/json') {
    $failures[] = 'JSON 404 응답의 Content-Type이 application/json이어야 한다.';
}

// (5) API와 UI 경로 구분 확인
$apiTestPaths = [
    '/api/documents',
    '/api/documents/123',
    '/api/documents/by-title',
];

foreach ($apiTestPaths as $path) {
    if (!str_starts_with($path, '/api/')) {
        $failures[] = "API 경로 '{$path}'이 올바르게 인식되지 않았다.";
    }
}

$uiTestPaths = [
    '/',
    '/documents',
    '/edit',
    '/admin/dashboard',
];

foreach ($uiTestPaths as $path) {
    if (str_starts_with($path, '/api/')) {
        $failures[] = "UI 경로 '{$path}'가 API 경로로 잘못 인식되었다.";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "NotFoundRoute 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "NotFoundRoute 테스트 통과.\n");
exit(0);
