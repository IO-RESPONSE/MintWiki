<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\RestorePage`의 동작을 확인하는 smoke test (태스크 0599).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 복구 page가 올바르게 렌더링되는지
 * 확인한다. 위험 작업 확인 컴포넌트와 파일 업로드 필드가 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\RestorePage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Ui\FormErrorSummary;
use MintWiki\Ui\AdminDangerConfirmation;
use MintWiki\Security\CsrfTokenService;

$failures = [];

// 테스트용 dependencies 생성
$escaper = new Escaper();
$layout = new Layout();
$csrfTokenService = new CsrfTokenService();
$formErrorSummary = new FormErrorSummary();
$dangerConfirmation = new AdminDangerConfirmation();
$page = new RestorePage($escaper, $layout, $csrfTokenService, $formErrorSummary, $dangerConfirmation);

// (1) 기본 복구 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '복구 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>데이터 복구</title>')) {
    $failures[] = '복구 page의 title이 "데이터 복구"이어야 한다.';
}

if (!str_contains($html, '<h1>데이터 복구</h1>')) {
    $failures[] = '복구 page가 h1으로 "데이터 복구"를 표시해야 한다.';
}

if (!str_contains($html, '<form method="post" action="/admin/restore"')) {
    $failures[] = '복구 page가 POST form을 포함해야 한다.';
}

if (!str_contains($html, 'enctype="multipart/form-data"')) {
    $failures[] = '복구 form이 파일 업로드를 지원하기 위해 multipart/form-data를 포함해야 한다.';
}

if (!str_contains($html, '<input type="hidden" name="csrf_token"')) {
    $failures[] = '복구 page가 CSRF 토큰 필드를 포함해야 한다.';
}

if (!str_contains($html, '<label for="backup_file">백업 파일</label>')) {
    $failures[] = '복구 page가 backup_file 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<input type="file" id="backup_file" name="backup_file"')) {
    $failures[] = '복구 page가 파일 업로드 필드를 포함해야 한다.';
}

if (!str_contains($html, 'accept=".json,.sql"')) {
    $failures[] = '파일 업로드 필드가 JSON과 SQL 파일만 허용해야 한다.';
}

if (!str_contains($html, '<button type="submit">복구</button>')) {
    $failures[] = '복구 page가 submit 버튼을 포함해야 한다.';
}

if (!str_contains($html, 'class="admin-danger-confirmation"')) {
    $failures[] = '복구 page가 위험 작업 확인 컴포넌트를 포함해야 한다.';
}

if (!str_contains($html, '데이터 복구')) {
    $failures[] = '위험 확인에 "데이터 복구" 제목이 포함되어야 한다.';
}

if (!str_contains($html, '현재 데이터베이스의 모든 데이터를 백업에서 로드된 데이터로 덮어쓰게 됩니다')) {
    $failures[] = '위험 확인에 경고 메시지가 포함되어야 한다.';
}

if (!str_contains($html, 'name="confirm_restore"')) {
    $failures[] = '위험 확인 체크박스가 confirm_restore 이름을 가져야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '복구 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '복구 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '복구 page가 footer landmark를 포함해야 한다.';
}

// (2) 폼 오류가 있는 경우 렌더링
$errors = ['backup_file' => '파일을 선택해야 합니다.'];
$htmlWithErrors = $page->render($errors);

if (!str_contains($htmlWithErrors, '오류가 발생했습니다')) {
    $failures[] = '폼 오류가 있을 때 오류 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithErrors, '파일을 선택해야 합니다.')) {
    $failures[] = '폼 오류가 있을 때 backup_file 오류 메시지를 표시해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "RestorePage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "RestorePage 테스트 통과.\n");
exit(0);
