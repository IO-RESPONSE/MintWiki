<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\BackupPage`의 동작을 확인하는 smoke test (태스크 0598).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 백업 page가 올바르게 렌더링되는지
 * 확인한다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\BackupPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new BackupPage($escaper, $layout);

// (1) 기본 백업 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '백업 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>백업</title>')) {
    $failures[] = '백업 page의 title이 "백업"이어야 한다.';
}

if (!str_contains($html, '<h1>백업</h1>')) {
    $failures[] = '백업 page가 h1으로 "백업"을 표시해야 한다.';
}

if (!str_contains($html, '<p>백업 및 복구 기능을 준비 중입니다.</p>')) {
    $failures[] = '백업 page가 준비 상태 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '백업 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '백업 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '백업 page가 footer landmark를 포함해야 한다.';
}

// (2) 백업 목록의 각 항목에 다운로드 링크가 노출되어야 한다 (태스크 0716).
$listHtml = $page->render(['mintwiki-backup-20260706-000000-abcd1234.json']);

if (!str_contains($listHtml, 'mintwiki-backup-20260706-000000-abcd1234.json')) {
    $failures[] = '백업 목록에 백업 파일명이 표시되어야 한다.';
}

if (!str_contains($listHtml, '/admin/backup/download/mintwiki-backup-20260706-000000-abcd1234.json')) {
    $failures[] = '백업 목록 각 항목에 다운로드 route로 향하는 링크가 있어야 한다.';
}

if (!str_contains($listHtml, '>다운로드</a>')) {
    $failures[] = '백업 목록 각 항목의 다운로드 링크에 "다운로드" 문구가 있어야 한다.';
}

// (3) 파일명은 escape되어야 한다 (XSS 방지).
$xssHtml = $page->render(['<script>alert(1)</script>.json']);
if (str_contains($xssHtml, '<script>alert(1)</script>')) {
    $failures[] = '백업 파일명이 escape되지 않은 채 렌더링되면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "BackupPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "BackupPage 테스트 통과.\n");
exit(0);
