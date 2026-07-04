<?php

declare(strict_types=1);

/**
 * MintWiki\App\ProductionErrorHandler의 production-safe 응답 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ProductionErrorHandler;
use MintWiki\Http\Request;

$failures = [];
$handler = new ProductionErrorHandler();
$exception = new RuntimeException('SQLSTATE[HY000] password=secret /srv/wiki/config.php');

$jsonResponse = $handler->handle(
    $exception,
    new Request('GET', '/api/documents', [], '', ['Accept' => 'application/json']),
    'req_test_123'
);

if ($jsonResponse->status() !== 500) {
    $failures[] = 'API production 오류 응답은 500 상태 코드여야 한다.';
}

if (($jsonResponse->headers()['Content-Type'] ?? '') !== 'application/json') {
    $failures[] = 'API production 오류 응답은 JSON Content-Type이어야 한다.';
}

if (($jsonResponse->headers()['X-Request-Id'] ?? '') !== 'req_test_123') {
    $failures[] = 'API production 오류 응답은 request id 헤더를 포함해야 한다.';
}

$jsonBody = json_decode($jsonResponse->body(), true);
if (!is_array($jsonBody)) {
    $failures[] = 'API production 오류 응답 body는 유효한 JSON이어야 한다.';
} else {
    $error = $jsonBody['error'] ?? null;
    if (!is_array($error)) {
        $failures[] = 'API production 오류 응답은 error 객체를 포함해야 한다.';
    } else {
        if (($error['code'] ?? '') !== 'app.internal_error') {
            $failures[] = 'API production 오류 code는 app.internal_error여야 한다.';
        }

        if (($error['message'] ?? '') !== '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.') {
            $failures[] = 'API production 오류 message는 안전한 사용자 메시지여야 한다.';
        }

        if (($error['request_id'] ?? '') !== 'req_test_123') {
            $failures[] = 'API production 오류는 request_id를 포함해야 한다.';
        }
    }
}

foreach (['SQLSTATE', 'password=secret', '/srv/wiki/config.php', 'trace', 'exception', 'sql'] as $leakedValue) {
    if (str_contains($jsonResponse->body(), $leakedValue)) {
        $failures[] = "API production 오류 응답이 내부 값 '{$leakedValue}'을 노출하면 안 된다.";
    }
}

$htmlResponse = $handler->handle(
    $exception,
    new Request('GET', '/documents'),
    'req_html_456'
);

if ($htmlResponse->status() !== 500) {
    $failures[] = 'HTML production 오류 응답은 500 상태 코드여야 한다.';
}

if (($htmlResponse->headers()['Content-Type'] ?? '') !== 'text/html; charset=utf-8') {
    $failures[] = 'HTML production 오류 응답은 HTML Content-Type이어야 한다.';
}

if (($htmlResponse->headers()['X-Request-Id'] ?? '') !== 'req_html_456') {
    $failures[] = 'HTML production 오류 응답은 request id 헤더를 포함해야 한다.';
}

if (!str_contains($htmlResponse->body(), '<h1>서버 오류</h1>')) {
    $failures[] = 'HTML production 오류 응답은 공통 서버 오류 page를 사용해야 한다.';
}

foreach (['SQLSTATE', 'password=secret', '/srv/wiki/config.php'] as $leakedValue) {
    if (str_contains($htmlResponse->body(), $leakedValue)) {
        $failures[] = "HTML production 오류 응답이 내부 값 '{$leakedValue}'을 노출하면 안 된다.";
    }
}

$acceptJsonResponse = $handler->handle(
    $exception,
    new Request('GET', '/documents', [], '', ['Accept' => 'text/html, application/json;q=0.9']),
    'req_accept_789'
);

if (($acceptJsonResponse->headers()['Content-Type'] ?? '') !== 'application/json') {
    $failures[] = 'Accept 헤더가 application/json을 포함하면 JSON 오류 응답이어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ProductionErrorHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ProductionErrorHandler 테스트 통과.\n");
exit(0);
