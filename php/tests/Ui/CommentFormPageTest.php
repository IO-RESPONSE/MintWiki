<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\CommentFormPage`의 동작을 확인하는 smoke test (태스크 0549).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 댓글 form이 올바르게 렌더링되는지
 * 확인한다. 폼 필드와 CSRF 토큰이 표시되어야 하고, 로그인하지 않은 경우
 * 로그인 필요 상태를 표시해야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\CommentFormPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Ui\FormErrorSummary;
use MintWiki\Security\CsrfTokenService;

$failures = [];

// 테스트용 dependencies 생성
$escaper = new Escaper();
$layout = new Layout();
$csrfTokenService = new CsrfTokenService();
$formErrorSummary = new FormErrorSummary();
$page = new CommentFormPage($escaper, $layout, $csrfTokenService, $formErrorSummary);

// (1) 기본 댓글 form 렌더링 (로그인한 경우)
$threadId = 'thread-123';
$html = $page->render($threadId);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '댓글 form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>댓글 작성</title>')) {
    $failures[] = '댓글 form의 title이 "댓글 작성"이어야 한다.';
}

if (!str_contains($html, '<h1>댓글 작성</h1>')) {
    $failures[] = '댓글 form이 h1으로 "댓글 작성"을 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/threads/thread-123/comments">')) {
    $failures[] = '댓글 form이 올바른 action을 가진 POST form을 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = '댓글 form이 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="body">댓글 본문</label>')) {
    $failures[] = '댓글 form이 body 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<textarea id="body" name="body" required></textarea>')) {
    $failures[] = '댓글 본문 필드가 textarea이고 필수(required)여야 한다.';
}

if (!str_contains($html, '<button type="submit">댓글 작성</button>')) {
    $failures[] = '댓글 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '댓글 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '댓글 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '댓글 form이 footer landmark를 포함해야 한다.';
}

// (2) 폼 오류가 있는 경우 렌더링
$errors = ['body' => '댓글 본문은 필수입니다.'];
$htmlWithErrors = $page->render($threadId, $errors);

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '댓글 본문은 필수입니다.')) {
    $failures[] = '폼 오류가 있을 때 body 오류 메시지를 표시해야 한다.';
}

// (3) 로그인하지 않은 경우 렌더링
$htmlUnauthorized = $page->render($threadId, [], false);

if (!str_contains($htmlUnauthorized, '로그인이 필요합니다')) {
    $failures[] = '로그인하지 않은 경우 로그인 필요 메시지를 표시해야 한다.';
}

if (!str_contains($htmlUnauthorized, '<a href="/login">로그인</a>')) {
    $failures[] = '로그인하지 않은 경우 로그인 링크를 표시해야 한다.';
}

// 로그인하지 않은 경우 form이 표시되지 않아야 한다
if (str_contains($htmlUnauthorized, '<form method="post"')) {
    $failures[] = '로그인하지 않은 경우 댓글 form을 표시하지 않아야 한다.';
}

// (4) thread_id escaping 테스트
$threadIdWithSpecialChars = 'thread<script>alert(1)</script>';
$htmlEscaped = $page->render($threadIdWithSpecialChars);

if (str_contains($htmlEscaped, '<script>')) {
    $failures[] = 'thread_id에 포함된 특수 문자가 escaped되지 않았다.';
}

if (!str_contains($htmlEscaped, 'thread&lt;script&gt;')) {
    $failures[] = 'thread_id가 올바르게 escaped되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "CommentFormPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "CommentFormPage 테스트 통과.\n");
exit(0);
