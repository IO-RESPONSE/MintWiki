<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\BlockUserFormPage`의 동작을 확인하는 smoke test (태스크 0547).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 사용자 차단 form이 올바르게 렌더링되는지
 * 확인한다. 폼 필드와 CSRF 토큰이 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\BlockUserFormPage;
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
$page = new BlockUserFormPage($escaper, $layout, $csrfTokenService, $formErrorSummary);

// (1) 기본 사용자 차단 form 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '사용자 차단 form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>사용자 차단</title>')) {
    $failures[] = '사용자 차단 form의 title이 "사용자 차단"이어야 한다.';
}

if (!str_contains($html, '<h1>사용자 차단</h1>')) {
    $failures[] = '사용자 차단 form이 h1으로 "사용자 차단"를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/admin/block-user">')) {
    $failures[] = '사용자 차단 form이 POST form을 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = '사용자 차단 form이 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="user_id">사용자 ID</label>')) {
    $failures[] = '사용자 차단 form이 user_id 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="user_id" name="user_id" required>')) {
    $failures[] = '사용자 ID 입력 필드가 필수(required)여야 한다.';
}

if (!str_contains($html, '<label for="reason">차단 사유</label>')) {
    $failures[] = '사용자 차단 form이 reason 필드를 포함해야 한다.';
}

if (!str_contains($html, '<textarea id="reason" name="reason" required></textarea>')) {
    $failures[] = '차단 사유 필드가 textarea이고 필수(required)여야 한다.';
}

if (!str_contains($html, '<button type="submit">차단</button>')) {
    $failures[] = '사용자 차단 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '사용자 차단 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '사용자 차단 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '사용자 차단 form이 footer landmark를 포함해야 한다.';
}

// (2) 폼 오류가 있는 경우 렌더링
$errors = ['user_id' => '사용자를 찾을 수 없습니다.', 'reason' => '차단 사유는 필수입니다.'];
$htmlWithErrors = $page->render($errors);

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '사용자를 찾을 수 없습니다.')) {
    $failures[] = '폼 오류가 있을 때 user_id 오류 메시지를 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '차단 사유는 필수입니다.')) {
    $failures[] = '폼 오류가 있을 때 reason 오류 메시지를 표시해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "BlockUserFormPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "BlockUserFormPage 테스트 통과.\n");
exit(0);
