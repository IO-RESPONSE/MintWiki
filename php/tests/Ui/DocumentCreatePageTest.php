<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentCreatePage`의 동작을 확인하는 smoke test (태스크 0530).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 새 문서 생성 form이 올바르게 렌더링되는지
 * 확인한다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\DocumentCreatePage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Security\CsrfTokenService;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

$csrfTokenService = new CsrfTokenService();
$page = new DocumentCreatePage($escaper, $layout, $csrfTokenService);

// (1) 기본 form 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '생성 form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>새 문서 만들기</title>')) {
    $failures[] = '생성 form의 title이 "새 문서 만들기"여야 한다.';
}

if (!str_contains($html, '<h1>새 문서 만들기</h1>')) {
    $failures[] = '생성 form이 h1으로 "새 문서 만들기"를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/documents">')) {
    $failures[] = '생성 form이 POST form을 포함해야 한다.';
}

// CSRF 토큰 확인
if (!preg_match('/<input type="hidden" name="csrf_token" value="[a-f0-9]{64}">/', $html)) {
    $failures[] = '생성 form이 CSRF 토큰 hidden input을 포함해야 한다.';
}

if (!str_contains($html, '<label for="title">제목</label>')) {
    $failures[] = '생성 form이 title label을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="title" name="title" required>')) {
    $failures[] = '생성 form이 title 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="source">내용</label>')) {
    $failures[] = '생성 form이 source label을 포함해야 한다.';
}

if (!str_contains($html, '<textarea id="source" name="source" required></textarea>')) {
    $failures[] = '생성 form이 source textarea를 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">저장</button>')) {
    $failures[] = '생성 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '생성 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '생성 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '생성 form이 footer landmark를 포함해야 한다.';
}

// (2) 각 render 호출마다 다른 CSRF 토큰 생성 확인
$_SESSION = [];
preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $html, $matches1);
$token1 = $matches1[1] ?? null;

$html2 = $page->render();
preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $html2, $matches2);
$token2 = $matches2[1] ?? null;

if ($token1 === null || $token2 === null) {
    $failures[] = 'CSRF 토큰이 올바른 형식이어야 한다.';
}

if ($token1 === $token2) {
    $failures[] = '각 render 호출마다 다른 CSRF 토큰을 생성해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentCreatePage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentCreatePage 테스트 통과.\n");
exit(0);
