<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 골격 (태스크 0394).
 *
 * 아직 라우팅이나 애플리케이션 로직은 연결되어 있지 않다 — 요청 정보만
 * 읽어 고정된 placeholder 응답을 반환한다. 실제 라우팅은 이후 태스크
 * (0398 route 등록 테스트, 0419 health endpoint, 0526 home page route
 * 등, `docs/php-db-ui-micro-job-prompts-0351-0670.md`)에서 이어진다.
 */

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'CLI';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';

$body = sprintf(
    "MintWiki PHP front controller placeholder\nmethod=%s\nuri=%s\n",
    $requestMethod,
    $requestUri
);

if (!headers_sent()) {
    header('Content-Type: text/plain; charset=utf-8');
    http_response_code(200);
}

echo $body;
