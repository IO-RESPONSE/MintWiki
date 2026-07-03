<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DiscussionPage`의 동작을 확인하는 smoke test (태스크 0548).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 스레드가 있는 경우와 없는 경우 모두
 * HTML 응답을 올바르게 렌더링하는지 확인한다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Thread;
use MintWiki\Document\Document;
use MintWiki\Ui\DiscussionPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper, layout, page 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new DiscussionPage($escaper, $layout);

// (1) 스레드가 없는 경우
$document = new Document('test-id', '테스트 문서', 'revision-1');
$html = $page->render($document, []);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '토론 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>문서 토론</title>')) {
    $failures[] = '토론 page의 title이 "문서 토론"이어야 한다.';
}

if (!str_contains($html, '<h1>테스트 문서 - 토론</h1>')) {
    $failures[] = '토론 page가 "문서 제목 - 토론" 제목을 h1으로 표시해야 한다.';
}

if (!str_contains($html, 'thread 없음')) {
    $failures[] = '스레드가 없을 때 "thread 없음" 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '토론 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '토론 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '토론 page가 footer landmark를 포함해야 한다.';
}

// (2) 스레드가 있는 경우
$now = new \DateTimeImmutable('2026-01-01T00:00:00Z');
$thread = new Thread('thread-1', 'test-id', '첫 번째 스레드', 'user1', $now, 'open');
$htmlWithThread = $page->render($document, [$thread]);

if (!str_contains($htmlWithThread, 'thread-1')) {
    $failures[] = '토론 page가 스레드 ID를 표시해야 한다.';
}

if (!str_contains($htmlWithThread, '첫 번째 스레드')) {
    $failures[] = '토론 page가 스레드 제목을 표시해야 한다.';
}

if (!str_contains($htmlWithThread, 'user1')) {
    $failures[] = '토론 page가 스레드 작성자를 표시해야 한다.';
}

if (!str_contains($htmlWithThread, 'open')) {
    $failures[] = '토론 page가 스레드 상태를 표시해야 한다.';
}

if (str_contains($htmlWithThread, 'thread 없음')) {
    $failures[] = '스레드가 있을 때 "thread 없음" 메시지를 표시하면 안 된다.';
}

// (3) 문서 제목에 XSS 공격이 포함된 경우 escape 확인
$xssDocument = new Document('xss-id', '<script>alert("xss")</script>', null);
$xssHtml = $page->render($xssDocument, []);

if (str_contains($xssHtml, '<script>')) {
    $failures[] = '문서 제목의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '문서 제목이 escape되어야 한다.';
}

// (4) 스레드 제목에 XSS 공격이 포함된 경우 escape 확인
$xssThread = new Thread('xss-thread', 'test-id', '<img src="x" onerror="alert(1)">', 'user1', $now);
$xssThreadHtml = $page->render($document, [$xssThread]);

if (str_contains($xssThreadHtml, '<img src=')) {
    $failures[] = '스레드 제목의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssThreadHtml, '&lt;img')) {
    $failures[] = '스레드 제목이 escape되어야 한다.';
}

// (5) 다른 특수 문자도 escape되는지 확인
$specialThread = new Thread('special-id', 'test-id', '스레드 & < > "제목"', 'user&name', $now);
$specialHtml = $page->render($document, [$specialThread]);

if (!str_contains($specialHtml, '스레드 &amp; &lt; &gt; &quot;제목&quot;')) {
    $failures[] = '스레드 제목의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'user&amp;name')) {
    $failures[] = '작성자 ID의 특수 문자들이 올바르게 escape되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DiscussionPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DiscussionPage 테스트 통과.\n");
exit(0);
