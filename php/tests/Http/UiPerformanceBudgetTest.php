<?php

declare(strict_types=1);

/**
 * UI 정적 자산(CSS, JavaScript)과 HTML 응답의 크기 예산을 검증하는 테스트.
 * 태스크 0580: 큰 번들 도입을 방지한다.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Layout;

$failures = [];
$basePath = __DIR__ . '/../../public/assets';

// 성능 예산 정의 (gzipped, bytes)
$budgets = [
    'html_layout' => 3072,    // 3 KB
    'css_total' => 15360,     // 15 KB
    'css_design_tokens' => 4096,   // 4 KB
    'css_buttons' => 2048,         // 2 KB
    'css_responsive_table' => 3072, // 3 KB
    'css_print' => 1024,           // 1 KB
    'js_total' => 5120,       // 5 KB
];

// Helper: 파일을 gzip 압축하고 크기를 반환한다
function getGzipSize(string $content): int {
    return strlen(gzcompress($content, 9));
}

// Helper: 파일을 읽고 gzip 크기를 반환한다
function getFileGzipSize(string $filePath): int {
    if (!is_file($filePath)) {
        return 0;
    }
    $content = file_get_contents($filePath);
    if ($content === false) {
        return 0;
    }
    return getGzipSize($content);
}

// 테스트 1: CSS 파일들의 개별 크기 확인
$cssFiles = [
    'design-tokens' => $basePath . '/css/design-tokens.css',
    'buttons' => $basePath . '/css/buttons.css',
    'responsive-table' => $basePath . '/css/responsive-table.css',
    'print' => $basePath . '/css/print.css',
];

$totalCssSize = 0;
foreach ($cssFiles as $name => $filePath) {
    $size = getFileGzipSize($filePath);
    $budgetKey = 'css_' . str_replace('-', '_', $name);
    $budget = $budgets[$budgetKey] ?? 5120; // 기본값 5KB

    if ($size > $budget) {
        $failures[] = "CSS 파일 '{$name}.css'의 크기({$size} bytes)가 예산({$budget} bytes)을 초과한다.";
    }
    $totalCssSize += $size;
}

// 테스트 2: CSS 총 크기 확인
if ($totalCssSize > $budgets['css_total']) {
    $failures[] = "CSS 총 크기({$totalCssSize} bytes)가 예산({$budgets['css_total']} bytes)을 초과한다.";
}

// 테스트 3: JavaScript 파일들의 총 크기 확인
$jsPath = $basePath . '/js';
$totalJsSize = 0;
if (is_dir($jsPath)) {
    $jsFiles = glob($jsPath . '/*.js');
    foreach ($jsFiles as $filePath) {
        $size = getFileGzipSize($filePath);
        $totalJsSize += $size;
    }
}

if ($totalJsSize > $budgets['js_total']) {
    $failures[] = "JavaScript 총 크기({$totalJsSize} bytes)가 예산({$budgets['js_total']} bytes)을 초과한다.";
}

// 테스트 4: 기본 HTML 레이아웃의 크기 확인
$layout = new Layout();
$htmlBody = '<main><h1>테스트</h1></main>';
$renderedHtml = $layout->render('MintWiki', $htmlBody);
$htmlSize = getGzipSize($renderedHtml);

if ($htmlSize > $budgets['html_layout']) {
    $failures[] = "HTML 레이아웃의 크기({$htmlSize} bytes)가 예산({$budgets['html_layout']} bytes)을 초과한다.";
}

// 테스트 5: 빈 body에 대한 레이아웃도 확인
$renderedMinimal = $layout->render('MintWiki', '');
$minimalSize = getGzipSize($renderedMinimal);

if ($minimalSize > $budgets['html_layout']) {
    $failures[] = "최소 HTML 레이아웃의 크기({$minimalSize} bytes)가 예산({$budgets['html_layout']} bytes)을 초과한다.";
}

// 테스트 6: Request ID를 포함한 레이아웃도 확인
$renderedWithId = $layout->render('MintWiki', '', 'ko', 'req-123456');
$withIdSize = getGzipSize($renderedWithId);

if ($withIdSize > $budgets['html_layout']) {
    $failures[] = "Request ID를 포함한 HTML 레이아웃의 크기({$withIdSize} bytes)가 예산({$budgets['html_layout']} bytes)을 초과한다.";
}

// 결과 출력
if ($failures !== []) {
    fwrite(STDERR, "UI 성능 예산 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    fwrite(STDERR, "\n성능 예산 현황 (gzipped):\n");
    fwrite(STDERR, "  HTML 레이아웃: {$htmlSize} / {$budgets['html_layout']} bytes\n");
    fwrite(STDERR, "  CSS 총합: {$totalCssSize} / {$budgets['css_total']} bytes\n");
    foreach ($cssFiles as $name => $filePath) {
        $size = getFileGzipSize($filePath);
        $budgetKey = 'css_' . str_replace('-', '_', $name);
        $budget = $budgets[$budgetKey] ?? 5120;
        fwrite(STDERR, "    - {$name}: {$size} / {$budget} bytes\n");
    }
    fwrite(STDERR, "  JavaScript 총합: {$totalJsSize} / {$budgets['js_total']} bytes\n");
    exit(1);
}

fwrite(STDOUT, "UI 성능 예산 테스트 통과.\n");
fwrite(STDOUT, "성능 예산 현황 (gzipped):\n");
fwrite(STDOUT, "  HTML 레이아웃: {$htmlSize} / {$budgets['html_layout']} bytes\n");
fwrite(STDOUT, "  CSS 총합: {$totalCssSize} / {$budgets['css_total']} bytes\n");
foreach ($cssFiles as $name => $filePath) {
    $size = getFileGzipSize($filePath);
    $budgetKey = 'css_' . str_replace('-', '_', $name);
    $budget = $budgets[$budgetKey] ?? 5120;
    fwrite(STDOUT, "    - {$name}: {$size} / {$budget} bytes\n");
}
fwrite(STDOUT, "  JavaScript 총합: {$totalJsSize} / {$budgets['js_total']} bytes\n");
exit(0);
