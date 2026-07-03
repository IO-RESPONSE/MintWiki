<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\FilePermissionDiagnosticsPage`의 동작을 확인하는 smoke test (태스크 0631).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 파일 권한 진단 page가 공유 호스팅에서
 * 확인해야 하는 파일/디렉터리 권한 항목을 표시하고 입력 값을 escape하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;
use MintWiki\Ui\FilePermissionDiagnosticsPage;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new FilePermissionDiagnosticsPage($escaper, $layout);

// (1) 기본 파일 권한 진단 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '파일 권한 진단 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>파일 권한 진단</title>')) {
    $failures[] = '파일 권한 진단 page의 title이 "파일 권한 진단"이어야 한다.';
}

if (!str_contains($html, '<h1>파일 권한 진단</h1>')) {
    $failures[] = '파일 권한 진단 page가 h1으로 "파일 권한 진단"을 표시해야 한다.';
}

if (!str_contains($html, '<section aria-label="파일 권한 상태">')) {
    $failures[] = '파일 권한 진단 page가 파일 권한 상태 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<th scope="col">대상</th>')) {
    $failures[] = '파일 권한 진단 page가 대상 column을 포함해야 한다.';
}

if (!str_contains($html, '<th scope="col">권장 권한</th>')) {
    $failures[] = '파일 권한 진단 page가 권장 권한 column을 포함해야 한다.';
}

foreach (['설정 파일', '캐시 디렉터리', '업로드 디렉터리', '로그 디렉터리'] as $label) {
    if (!str_contains($html, $label)) {
        $failures[] = "파일 권한 진단 page가 {$label} 항목을 포함해야 한다.";
    }
}

if (!str_contains($html, '<a href="/admin/status">운영 진단으로 돌아가기</a>')) {
    $failures[] = '파일 권한 진단 page가 운영 진단 page로 돌아가는 링크를 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '파일 권한 진단 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '파일 권한 진단 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '파일 권한 진단 page가 footer landmark를 포함해야 한다.';
}

// (2) 전달받은 진단 row가 escape되는지 확인
$escapedHtml = $page->render([
    [
        'label' => '설정 <파일>',
        'path' => 'php/config/<local>.php',
        'expected' => '쓰기 금지 & 읽기 허용',
        'status' => '<script>alert(1)</script>',
        'detail' => '권한은 0644보다 넓으면 안 됩니다.',
    ],
]);

if (str_contains($escapedHtml, '<script>alert(1)</script>')) {
    $failures[] = '파일 권한 진단 page가 상태 필드에서 script 태그를 escape해야 한다.';
}

if (!str_contains($escapedHtml, '설정 &lt;파일&gt;')) {
    $failures[] = '파일 권한 진단 page가 대상 필드의 <와 >를 escape해야 한다.';
}

if (!str_contains($escapedHtml, 'php/config/&lt;local&gt;.php')) {
    $failures[] = '파일 권한 진단 page가 경로 필드의 <와 >를 escape해야 한다.';
}

if (!str_contains($escapedHtml, '쓰기 금지 &amp; 읽기 허용')) {
    $failures[] = '파일 권한 진단 page가 권장 권한 필드의 앰퍼샌드를 escape해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "FilePermissionDiagnosticsPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FilePermissionDiagnosticsPage 테스트 통과.\n");
exit(0);
