<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DiscussionPage`의 동작을 확인하는 smoke test (태스크 0548,
 * 댓글/새 스레드 폼 주입은 0712).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 스레드가 있는 경우와 없는 경우 모두
 * HTML 응답을 올바르게 렌더링하는지 확인한다. 0712에서 각 스레드의 댓글
 * 목록과 댓글 작성 form(`CommentFormPage::renderForm()` 조각), 새 스레드를
 * 시작하는 form을 함께 렌더링하도록 확장했다 — `$isAuthorized`가 false면
 * 두 form 모두 로그인 안내로 대체된다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
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

if (!str_contains($html, '<footer>')) {
    $failures[] = '토론 page가 footer landmark를 포함해야 한다.';
}

// (1-b) 새 스레드 form이 항상 포함되어야 한다(로그인한 경우 기본값).
if (!str_contains($html, '<h2>새 토론 시작하기</h2>')) {
    $failures[] = '토론 page가 새 스레드 시작 form 섹션을 포함해야 한다.';
}

if (!str_contains($html, 'action="/wiki/%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EB%AC%B8%EC%84%9C/discussion"')) {
    $failures[] = '새 스레드 form의 action은 /wiki/{title}/discussion을 가리켜야 한다.';
}

if (!preg_match('/name="csrf_token" value="[a-f0-9]{64}"/', $html)) {
    $failures[] = '새 스레드 form은 CSRF 토큰 hidden input을 포함해야 한다.';
}

// (2) 스레드가 있는 경우 (댓글 없음 -> "댓글 없음" 빈 상태 + 댓글 form 포함)
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

if (!str_contains($htmlWithThread, '댓글 없음')) {
    $failures[] = '댓글이 없는 스레드는 "댓글 없음" 메시지를 표시해야 한다.';
}

if (!str_contains($htmlWithThread, 'action="/wiki/%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EB%AC%B8%EC%84%9C/discussion/thread-1/comment"')) {
    $failures[] = '스레드마다 그 스레드의 댓글 작성 form(action=/wiki/{title}/discussion/{threadId}/comment)이 포함되어야 한다.';
}

// (2-b) 스레드에 댓글이 있는 경우 댓글 목록이 렌더링되어야 한다.
$comment = new Comment('comment-1', 'thread-1', '첫 댓글 내용', 'user2', $now);
$htmlWithComment = $page->render($document, [$thread], ['thread-1' => [$comment]]);

if (str_contains($htmlWithComment, '댓글 없음')) {
    $failures[] = '댓글이 있으면 "댓글 없음" 메시지를 표시하면 안 된다.';
}

if (!str_contains($htmlWithComment, '첫 댓글 내용') || !str_contains($htmlWithComment, 'user2')) {
    $failures[] = '토론 page가 댓글 본문과 작성자를 표시해야 한다.';
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

// (4-b) 댓글 본문에 XSS 공격이 포함된 경우 escape 확인
$xssComment = new Comment('xss-comment', 'thread-1', '<script>alert("comment-xss")</script>', 'user1', $now);
$xssCommentHtml = $page->render($document, [$thread], ['thread-1' => [$xssComment]]);

if (str_contains($xssCommentHtml, '<script>alert("comment-xss")')) {
    $failures[] = '댓글 본문의 script 태그는 escape되어야 한다.';
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

// (6) 새 스레드 form 검증 오류 표시
$htmlWithErrors = $page->render($document, [], [], ['title' => '스레드 제목을 입력하세요.']);
if (!str_contains($htmlWithErrors, '스레드 제목을 입력하세요.')) {
    $failures[] = '새 스레드 form 검증 오류가 표시되어야 한다.';
}

// (7) $isAuthorized가 false면 새 스레드/댓글 form 대신 로그인 안내를 보여줘야 한다.
$htmlUnauthorized = $page->render($document, [$thread], [], [], [], false);

if (str_contains($htmlUnauthorized, '<form method="post"')) {
    $failures[] = '토론 쓰기 권한이 없으면 새 스레드/댓글 form을 표시하면 안 된다.';
}

if (!str_contains($htmlUnauthorized, '로그인이 필요합니다')) {
    $failures[] = '토론 쓰기 권한이 없으면 로그인 필요 안내를 표시해야 한다.';
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
