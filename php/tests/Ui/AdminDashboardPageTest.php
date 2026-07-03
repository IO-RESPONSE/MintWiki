<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AdminDashboardPage`의 동작을 확인하는 smoke test (태스크 0544).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 관리자 대시보드 page가 올바르게 렌더링되는지
 * 확인한다. 시스템 상태, 신고, 감사 링크가 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AdminDashboardPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new AdminDashboardPage($escaper, $layout);

// (1) 기본 관리자 대시보드 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '관리자 대시보드 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>관리자 대시보드</title>')) {
    $failures[] = '관리자 대시보드 page의 title이 "관리자 대시보드"이어야 한다.';
}

if (!str_contains($html, '<h1>관리자 대시보드</h1>')) {
    $failures[] = '관리자 대시보드 page가 h1으로 "관리자 대시보드"를 표시해야 한다.';
}

if (!str_contains($html, '<a href="/admin/status">시스템 상태</a>')) {
    $failures[] = '관리자 대시보드 page가 시스템 상태 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/reporting">신고</a>')) {
    $failures[] = '관리자 대시보드 page가 신고 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/audit">감사</a>')) {
    $failures[] = '관리자 대시보드 page가 감사 링크를 포함해야 한다.';
}

if (!str_contains($html, '<nav aria-label="관리 기능">')) {
    $failures[] = '관리자 대시보드 page가 관리 기능 navigation을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '관리자 대시보드 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '관리자 대시보드 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '관리자 대시보드 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AdminDashboardPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminDashboardPage 테스트 통과.\n");
exit(0);
