<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallSchemaApplyPage`의 동작을 확인하는 smoke test (태스크 0680).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 스키마 적용 진행 화면이 올바르게
 * 렌더링되는지 확인한다. CSRF 토큰과 제출 form이 표시되어야 하고, 오류가
 * 있으면 오류 메시지가 escaping되어 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\InstallSchemaApplyPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Security\CsrfTokenService;

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$csrfTokenService = new CsrfTokenService();
$page = new InstallSchemaApplyPage($escaper, $layout, $csrfTokenService);

// (1) 기본 진행 화면 렌더링(오류 없음)
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '스키마 적용 화면 HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>데이터베이스 스키마 적용</title>')) {
    $failures[] = '스키마 적용 화면의 title이 "데이터베이스 스키마 적용"이어야 한다.';
}

if (!str_contains($html, '<h1>데이터베이스 스키마 적용</h1>')) {
    $failures[] = '스키마 적용 화면이 h1으로 "데이터베이스 스키마 적용"을 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/install/schema">')) {
    $failures[] = '스키마 적용 화면이 올바른 action을 가진 POST form을 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = '스키마 적용 화면이 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<button type="submit">스키마 적용</button>')) {
    $failures[] = '스키마 적용 화면이 submit 버튼을 포함해야 한다.';
}

if (str_contains($html, 'role="alert"')) {
    $failures[] = '오류가 없을 때는 오류 요약이 표시되면 안 된다.';
}

// (2) 오류가 있는 경우 렌더링
$htmlWithError = $page->render('스키마 적용에 실패했습니다: 테스트용 오류');

if (!str_contains($htmlWithError, 'role="alert"')) {
    $failures[] = '오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithError, '테스트용 오류')) {
    $failures[] = '오류가 있을 때 오류 메시지 내용을 표시해야 한다.';
}

// (3) 오류 메시지 escaping 테스트
$htmlEscaped = $page->render('<script>alert(1)</script>');

if (str_contains($htmlEscaped, '<script>')) {
    $failures[] = '오류 메시지에 포함된 특수 문자가 escaped되지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallSchemaApplyPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallSchemaApplyPage 테스트 통과.\n");
exit(0);
