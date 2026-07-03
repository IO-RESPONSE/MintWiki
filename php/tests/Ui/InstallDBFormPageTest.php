<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallDBFormPage`의 동작을 확인하는 smoke test (태스크 0621).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. DB 설정 form이 올바르게 렌더링되는지
 * 확인한다. form 필드와 CSRF 토큰이 표시되어야 하고, MariaDB 연결 정보를
 * 입력받을 수 있어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\InstallDBFormPage;
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
$page = new InstallDBFormPage($escaper, $layout, $csrfTokenService, $formErrorSummary);

// (1) 기본 DB form 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = 'DB form HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>데이터베이스 설정</title>')) {
    $failures[] = 'DB form의 title이 "데이터베이스 설정"이어야 한다.';
}

if (!str_contains($html, '<h1>데이터베이스 설정</h1>')) {
    $failures[] = 'DB form이 h1으로 "데이터베이스 설정"을 표시해야 한다.';
}

if (!str_contains($html, '<p>MariaDB 데이터베이스 연결 정보를 입력하세요.</p>')) {
    $failures[] = 'DB form이 절차 안내 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/install/db">')) {
    $failures[] = 'DB form이 올바른 action을 가진 POST form을 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = 'DB form이 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="dsn">호스트명:포트</label>')) {
    $failures[] = 'DB form이 dsn 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="dsn" name="dsn"')) {
    $failures[] = 'DB form이 dsn 텍스트 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, 'placeholder="localhost:3306"')) {
    $failures[] = 'DB form의 dsn 필드가 placeholder를 가져야 한다.';
}

if (!str_contains($html, '<label for="username">사용자명</label>')) {
    $failures[] = 'DB form이 username 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="text" id="username" name="username"')) {
    $failures[] = 'DB form이 username 텍스트 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, 'placeholder="root"')) {
    $failures[] = 'DB form의 username 필드가 placeholder를 가져야 한다.';
}

if (!str_contains($html, '<label for="password">비밀번호</label>')) {
    $failures[] = 'DB form이 password 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="password" id="password" name="password"')) {
    $failures[] = 'DB form이 password 비밀번호 입력 필드를 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">데이터베이스 연결</button>')) {
    $failures[] = 'DB form이 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = 'DB form이 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = 'DB form이 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = 'DB form이 footer landmark를 포함해야 한다.';
}

// (2) 폼 오류가 있는 경우 렌더링
$errors = ['dsn' => 'DSN은 필수입니다.', 'password' => '비밀번호는 필수입니다.'];
$htmlWithErrors = $page->render($errors);

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, 'DSN은 필수입니다.')) {
    $failures[] = '폼 오류가 있을 때 dsn 오류 메시지를 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '비밀번호는 필수입니다.')) {
    $failures[] = '폼 오류가 있을 때 password 오류 메시지를 표시해야 한다.';
}

// (3) dsn escaping 테스트
$page2 = new InstallDBFormPage(new Escaper(), $layout, $csrfTokenService, $formErrorSummary);
$errors2 = ['dsn' => 'DSN<script>alert(1)</script>'];
$htmlEscaped = $page2->render($errors2);

if (str_contains($htmlEscaped, '<script>')) {
    $failures[] = 'dsn 오류 메시지에 포함된 특수 문자가 escaped되지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallDBFormPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallDBFormPage 테스트 통과.\n");
exit(0);
