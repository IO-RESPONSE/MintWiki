<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\ErrorPage`의 동작을 확인하는 smoke test (태스크 0592).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 404와 500 오류 page가 올바르게
 * 렌더링되는지 확인한다. 모든 동적 내용은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$page = new ErrorPage($escaper, $layout);

// (1) 404 page 렌더링 - 기본
$html = $page->renderNotFound();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '404 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>페이지를 찾을 수 없습니다</title>')) {
    $failures[] = '404 page의 title이 "페이지를 찾을 수 없습니다"이어야 한다.';
}

if (!str_contains($html, '<h1>페이지를 찾을 수 없습니다</h1>')) {
    $failures[] = '404 page가 h1으로 "페이지를 찾을 수 없습니다"를 표시해야 한다.';
}

if (!str_contains($html, '<p>요청한 페이지가 존재하지 않습니다.</p>')) {
    $failures[] = '404 page가 기본 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '404 page가 main 요소를 포함해야 한다.';
}

// (2) 404 page 렌더링 - 경로 포함
$html404WithPath = $page->renderNotFound('/api/documents/unknown');

if (!str_contains($html404WithPath, '/api/documents/unknown')) {
    $failures[] = '404 page가 요청 경로를 표시해야 한다.';
}

if (!str_contains($html404WithPath, '<dt>요청 경로:</dt>')) {
    $failures[] = '404 page가 "요청 경로:" 레이블을 포함해야 한다.';
}

if (!str_contains($html404WithPath, '<code>/api/documents/unknown</code>')) {
    $failures[] = '404 page가 경로를 code 요소로 감싸야 한다.';
}

// (3) 500 page 렌더링 - 기본
$html500 = $page->renderServerError();

if (!str_contains($html500, '<!doctype html>')) {
    $failures[] = '500 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html500, '<title>서버 오류</title>')) {
    $failures[] = '500 page의 title이 "서버 오류"이어야 한다.';
}

if (!str_contains($html500, '<h1>서버 오류</h1>')) {
    $failures[] = '500 page가 h1으로 "서버 오류"를 표시해야 한다.';
}

if (!str_contains($html500, '<p>서버 오류가 발생했습니다.</p>')) {
    $failures[] = '500 page가 기본 메시지를 표시해야 한다.';
}

// (4) 500 page 렌더링 - 메시지 포함
$html500WithMsg = $page->renderServerError('Database connection failed');

if (!str_contains($html500WithMsg, 'Database connection failed')) {
    $failures[] = '500 page가 오류 메시지를 표시해야 한다.';
}

if (!str_contains($html500WithMsg, '<dt>오류 메시지:</dt>')) {
    $failures[] = '500 page가 "오류 메시지:" 레이블을 포함해야 한다.';
}

// (5) XSS 방지 확인 - 404 페이지 경로 escaping
$xssPath = '/api/documents/<script>alert("xss")</script>';
$xssHtml404 = $page->renderNotFound($xssPath);

if (str_contains($xssHtml404, '<script>')) {
    $failures[] = '404 page가 경로 필드에서 script 태그를 escape해야 한다.';
}

if (!str_contains($xssHtml404, '&lt;script&gt;')) {
    $failures[] = '404 page가 경로의 <를 &lt;로 escape해야 한다.';
}

// (6) XSS 방지 확인 - 500 페이지 메시지 escaping
$xssMessage = 'Error: <img src=x onerror="alert(1)">';
$xssHtml500 = $page->renderServerError($xssMessage);

if (str_contains($xssHtml500, 'onerror="alert(1)"')) {
    $failures[] = '500 page가 메시지 필드에서 onerror를 escape해야 한다.';
}

if (!str_contains($xssHtml500, '&lt;img')) {
    $failures[] = '500 page가 메시지의 <를 &lt;로 escape해야 한다.';
}

// (7) Layout integration 확인
if (!str_contains($html, '<header></header>')) {
    $failures[] = '404 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '404 page가 footer landmark를 포함해야 한다.';
}

if (!str_contains($html500, '<header></header>')) {
    $failures[] = '500 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html500, '<footer>')) {
    $failures[] = '500 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ErrorPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ErrorPage 테스트 통과.\n");
exit(0);
