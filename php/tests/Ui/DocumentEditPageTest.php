<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentEditPage`의 동작을 확인하는 smoke test (태스크 0532).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 편집 form이 올바르게 렌더링되는지
 * 확인한다. title과 source가 기존 값으로 pre-fill되어야 하고, 모든 사용자 입력은
 * escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Ui\DocumentEditPage;
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
$page = new DocumentEditPage($escaper, $layout, $csrfTokenService);

// (1) 기본 편집 form 렌더링
$document = new Document('doc-123', '테스트 문서', 'revision-1');
$source = '# 테스트 문서의 내용\n\n이것은 예제입니다.';
$html = $page->render($document, $source);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '편집 form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>문서 편집</title>')) {
    $failures[] = '편집 form의 title이 "문서 편집"이어야 한다.';
}

if (!str_contains($html, '<h1>문서 편집</h1>')) {
    $failures[] = '편집 form이 h1으로 "문서 편집"를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/documents/doc-123">')) {
    $failures[] = '편집 form이 POST form을 포함해야 하고, 정확한 document id를 사용해야 한다.';
}

// CSRF 토큰 확인
if (!preg_match('/<input type="hidden" name="csrf_token" value="[a-f0-9]{64}">/', $html)) {
    $failures[] = '편집 form이 CSRF 토큰 hidden input을 포함해야 한다.';
}

if (!str_contains($html, '<label for="title">제목</label>')) {
    $failures[] = '편집 form이 title label을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="title" name="title" value="테스트 문서" required>')) {
    $failures[] = '편집 form이 title 입력 필드에 기존 값을 포함해야 한다.';
}

if (!str_contains($html, '<label for="source">내용</label>')) {
    $failures[] = '편집 form이 source label을 포함해야 한다.';
}

if (!str_contains($html, 'textarea id="source" name="source" required')) {
    $failures[] = '편집 form이 source textarea를 포함해야 한다.';
}

if (!str_contains($html, $source)) {
    $failures[] = '편집 form이 source textarea에 기존 값을 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">저장</button>')) {
    $failures[] = '편집 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '편집 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '편집 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '편집 form이 footer landmark를 포함해야 한다.';
}

// (2) 문서 제목에 XSS 공격이 포함된 경우 escape 확인
$xssDocument = new Document('xss-id', '<script>alert("xss")</script>', null);
$xssSource = '<img src=x onerror="alert(\'xss\')">';
$xssHtml = $page->render($xssDocument, $xssSource);

// title value에서 script 태그가 unescaped로 나타나면 안 됨
if (preg_match('/value="[^"]*<script/', $xssHtml)) {
    $failures[] = '문서 제목의 script 태그는 escape되어야 한다.';
}

// title value에서 &lt;script&gt; 형태로 escape되어야 함
if (!preg_match('/value="[^"]*&lt;script/', $xssHtml)) {
    $failures[] = '문서 제목이 escape되어야 한다.';
}

// textarea 안의 content에서 img 태그가 &lt;img로 escape되어야 함
if (!str_contains($xssHtml, '&lt;img src=x onerror=')) {
    $failures[] = 'source가 escape되어야 한다.';
}

// (3) source가 null인 경우
$noSourceHtml = $page->render($document, null);

if (!str_contains($noSourceHtml, '<textarea id="source" name="source" required></textarea>')) {
    $failures[] = 'source가 null일 때 textarea는 비어있어야 한다.';
}

// (4) 다른 특수 문자도 escape되는지 확인
$specialDocument = new Document('special-id', '문서 & < > "test"', null);
$specialSource = '내용 & < > "quote"';
$specialHtml = $page->render($specialDocument, $specialSource);

if (!str_contains($specialHtml, 'value="문서 &amp; &lt; &gt; &quot;test&quot;"')) {
    $failures[] = 'title의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, '내용 &amp; &lt; &gt; &quot;quote&quot;')) {
    $failures[] = 'source의 특수 문자들이 올바르게 escape되어야 한다.';
}

// (5) Document id도 escape되어야 한다
$specialIdDocument = new Document('id-&-test', '테스트', null);
$specialIdHtml = $page->render($specialIdDocument);

if (!str_contains($specialIdHtml, 'action="/documents/id-&amp;-test"')) {
    $failures[] = 'Document id가 form action에서 escape되어야 한다.';
}

// (6) 각 render 호출마다 다른 CSRF 토큰 생성 확인
$_SESSION = [];
preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $html, $matches1);
$token1 = $matches1[1] ?? null;

$html2 = $page->render($document, $source);
preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $html2, $matches2);
$token2 = $matches2[1] ?? null;

if ($token1 === null || $token2 === null) {
    $failures[] = 'CSRF 토큰이 올바른 형식이어야 한다.';
}

if ($token1 === $token2) {
    $failures[] = '각 render 호출마다 다른 CSRF 토큰을 생성해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentEditPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentEditPage 테스트 통과.\n");
exit(0);
