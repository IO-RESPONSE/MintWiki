<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\LoginPage`의 동작을 확인하는 smoke test (태스크 0538).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 로그인 page가 올바르게 렌더링되는지
 * 확인한다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\LoginPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new LoginPage($escaper, $layout);

// (1) 기본 로그인 page 렌더링
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

if (!str_contains($html, '<p>인증 준비 중입니다.</p>')) {
    $failures[] = '로그인 page가 준비 상태 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '로그인 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '로그인 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '로그인 page가 footer landmark를 포함해야 한다.';
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
