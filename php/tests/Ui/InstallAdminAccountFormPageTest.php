<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallAdminAccountFormPage`의 동작을 확인하는 smoke test (태스크 0624).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 최초 관리자 계정 생성 form이
 * 올바르게 렌더링되고 CSRF 토큰과 오류 요약을 포함하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\FormErrorSummary;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\Layout;

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$csrfTokenService = new CsrfTokenService();
$formErrorSummary = new FormErrorSummary();
$page = new InstallAdminAccountFormPage($escaper, $layout, $csrfTokenService, $formErrorSummary);

// (1) 기본 관리자 계정 form 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '관리자 계정 form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>관리자 계정 생성</title>')) {
    $failures[] = '관리자 계정 form의 title이 "관리자 계정 생성"이어야 한다.';
}

if (!str_contains($html, '<h1>관리자 계정 생성</h1>')) {
    $failures[] = '관리자 계정 form이 h1으로 "관리자 계정 생성"을 표시해야 한다.';
}

if (!str_contains($html, '<p>MintWiki 최초 관리자 계정 정보를 입력하세요.</p>')) {
    $failures[] = '관리자 계정 form이 안내 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/install/admin">')) {
    $failures[] = '관리자 계정 form이 올바른 action을 가진 POST form을 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = '관리자 계정 form이 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="username">관리자 ID</label>')) {
    $failures[] = '관리자 계정 form이 username 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="username" name="username" autocomplete="username" required>')) {
    $failures[] = '관리자 계정 form이 username 텍스트 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="email">이메일</label>')) {
    $failures[] = '관리자 계정 form이 email 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="email" id="email" name="email" autocomplete="email" required>')) {
    $failures[] = '관리자 계정 form이 email 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="password">비밀번호</label>')) {
    $failures[] = '관리자 계정 form이 password 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="password" id="password" name="password" autocomplete="new-password" required>')) {
    $failures[] = '관리자 계정 form이 password 비밀번호 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="password_confirm">비밀번호 확인</label>')) {
    $failures[] = '관리자 계정 form이 password_confirm 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="password" id="password_confirm" name="password_confirm" autocomplete="new-password" required>')) {
    $failures[] = '관리자 계정 form이 password_confirm 비밀번호 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">관리자 계정 생성</button>')) {
    $failures[] = '관리자 계정 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '관리자 계정 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '관리자 계정 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '관리자 계정 form이 footer landmark를 포함해야 한다.';
}

// (2) 폼 오류가 있는 경우 렌더링
$errors = [
    'username' => '관리자 ID는 필수입니다.',
    'password_confirm' => '비밀번호 확인이 일치하지 않습니다.',
];
$htmlWithErrors = $page->render($errors);

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '관리자 ID는 필수입니다.')) {
    $failures[] = '폼 오류가 있을 때 username 오류 메시지를 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '비밀번호 확인이 일치하지 않습니다.')) {
    $failures[] = '폼 오류가 있을 때 password_confirm 오류 메시지를 표시해야 한다.';
}

// (3) 오류 메시지 escaping 테스트
$htmlEscaped = $page->render(['username' => '관리자<script>alert(1)</script>']);

if (str_contains($htmlEscaped, '<script>')) {
    $failures[] = 'username 오류 메시지에 포함된 특수 문자가 escaped되지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallAdminAccountFormPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallAdminAccountFormPage 테스트 통과.\n");
exit(0);
