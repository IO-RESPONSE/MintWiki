<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\WebCacheClearPage`의 동작을 확인하는 smoke test (태스크 0648).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 웹 캐시 초기화 placeholder가 관리자 전용
 * 안내와 placeholder 상태를 표시하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Ui\WebCacheClearPage;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new WebCacheClearPage($escaper, $layout);

// (1) 기본 웹 캐시 초기화 page 렌더링
$html = $page->render();

if (WebCacheClearPage::REQUIRED_PERMISSION !== 'admin:read') {
    $failures[] = '웹 캐시 초기화 page는 admin:read 권한을 요구해야 한다.';
}

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '웹 캐시 초기화 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>웹 캐시 초기화</title>')) {
    $failures[] = '웹 캐시 초기화 page의 title이 "웹 캐시 초기화"이어야 한다.';
}

if (!str_contains($html, '<h1>웹 캐시 초기화</h1>')) {
    $failures[] = '웹 캐시 초기화 page가 h1으로 "웹 캐시 초기화"를 표시해야 한다.';
}

if (!str_contains($html, '<section aria-label="웹 캐시 초기화 상태">')) {
    $failures[] = '웹 캐시 초기화 page가 상태 section을 포함해야 한다.';
}

if (!str_contains($html, '<p>관리자 전용 웹 캐시 초기화 기능을 준비 중입니다.</p>')) {
    $failures[] = '웹 캐시 초기화 page가 관리자 전용 준비 상태 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<p>placeholder</p>')) {
    $failures[] = '웹 캐시 초기화 page가 placeholder를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/status">운영 진단으로 돌아가기</a>')) {
    $failures[] = '웹 캐시 초기화 page가 운영 진단 복귀 링크를 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '웹 캐시 초기화 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '웹 캐시 초기화 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '웹 캐시 초기화 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "WebCacheClearPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "WebCacheClearPage 테스트 통과.\n");
exit(0);
