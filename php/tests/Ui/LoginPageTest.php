<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\LoginPage`의 동작을 확인하는 smoke test (태스크 0538, 실제 폼
 * 연결은 0686).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 로그인 form(아이디·비밀번호,
 * CSRF 토큰)이 올바르게 렌더링되고, 오류 요약과 escaping이 동작하는지
 * 확인한다.
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
use MintWiki\Ui\LoginPage;
use MintWiki\Ui\Layout;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$csrfTokenService = new CsrfTokenService();
$formErrorSummary = new FormErrorSummary();
$page = new LoginPage($escaper, $layout, $csrfTokenService, $formErrorSummary);

// (1) 기본 로그인 form 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '로그인 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>로그인</title>')) {
    $failures[] = '로그인 page의 title이 "로그인"이어야 한다.';
}

if (!str_contains($html, '<h1>로그인</h1>')) {
    $failures[] = '로그인 page가 h1으로 "로그인"을 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/login">')) {
    $failures[] = '로그인 form이 올바른 action을 가진 POST form을 포함해야 한다.';
}

if (!preg_match('/name="csrf_token" value="[a-f0-9]{64}"/', $html)) {
    $failures[] = '로그인 form이 CSRF 토큰 hidden input을 포함해야 한다.';
}

if (!str_contains($html, '<label for="username">아이디</label>')) {
    $failures[] = '로그인 form이 username 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="username" name="username" autocomplete="username" value="" required>')) {
    $failures[] = '로그인 form이 username 텍스트 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="password">비밀번호</label>')) {
    $failures[] = '로그인 form이 password 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="password" id="password" name="password" autocomplete="current-password" required>')) {
    $failures[] = '로그인 form이 password 비밀번호 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">로그인</button>')) {
    $failures[] = '로그인 form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '로그인 form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '로그인 form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '로그인 form이 footer landmark를 포함해야 한다.';
}

// (2) 오류가 있는 경우 렌더링 + 아이디값 유지 (비밀번호는 절대 채우지 않는다)
$htmlWithErrors = $page->render(['_form' => '아이디 또는 비밀번호가 올바르지 않습니다.'], 'admin');

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '아이디 또는 비밀번호가 올바르지 않습니다.')) {
    $failures[] = '폼 오류가 있을 때 오류 메시지를 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, 'id="username" name="username" autocomplete="username" value="admin"')) {
    $failures[] = '오류로 되돌아온 폼은 이전에 입력한 아이디값을 유지해야 한다.';
}

if (str_contains($htmlWithErrors, 'id="password"' . ' value="')) {
    $failures[] = '오류로 되돌아온 폼이라도 비밀번호 입력 필드를 값으로 채우면 안 된다.';
}

// (3) 오류 메시지/아이디 escaping 테스트
$htmlEscaped = $page->render(['_form' => '오류<script>alert(1)</script>'], '관리자<script>alert(2)</script>');

if (str_contains($htmlEscaped, '<script>')) {
    $failures[] = '오류 메시지 또는 아이디값에 포함된 특수 문자가 escaped되지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "LoginPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LoginPage 테스트 통과.\n");
exit(0);
