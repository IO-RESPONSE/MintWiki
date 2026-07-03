<?php

declare(strict_types=1);

/**
 * 모바일 CSS 존재 및 반응형 특성을 확인하는 테스트.
 *
 * viewport 메타 태그가 모바일 기기를 지원하도록 설정되었는지 확인한다.
 * CSS 파일에 모바일 대응 media query(@media)가 포함되어 있는지 검증한다.
 * 레이아웃 렌더링에서 viewport 설정을 확인하고,
 * CSS 파일들에 모바일 및 반응형 media query가 정의되었는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Layout;

$failures = [];
$layout = new Layout();

// ============================================================================
// 1. 레이아웃의 viewport 메타 태그 확인
// ============================================================================

$html = $layout->render('모바일 테스트', '<main><h1>테스트</h1></main>');

// (1-1) viewport 메타 태그가 존재해야 한다.
if (!str_contains($html, '<meta name="viewport"')) {
    $failures[] = '[viewport] 레이아웃이 viewport 메타 태그를 포함해야 한다.';
}

// (1-2) device-width 설정이 있어야 한다 (모바일 반응형 필수).
if (!str_contains($html, 'width=device-width')) {
    $failures[] = '[viewport] viewport이 width=device-width 설정을 포함해야 한다.';
}

// (1-3) initial-scale=1 설정이 있어야 한다.
if (!str_contains($html, 'initial-scale=1')) {
    $failures[] = '[viewport] viewport이 initial-scale=1 설정을 포함해야 한다.';
}

// (1-4) 전체 viewport 메타 태그 내용 확인
if (!str_contains($html, '<meta name="viewport" content="width=device-width, initial-scale=1">')) {
    $failures[] = '[viewport] viewport 메타 태그의 전체 속성이 올바르게 설정되어야 한다.';
}

// ============================================================================
// 2. CSS 파일의 모바일 media query 확인
// ============================================================================

$cssPath = __DIR__ . '/../../public/assets/css/responsive-table.css';

if (!is_file($cssPath)) {
    $failures[] = '[media-query] responsive-table.css 파일이 존재해야 한다.';
} else {
    $cssContent = file_get_contents($cssPath);

    // (2-1) 모바일 media query 확인 (max-width: 640px)
    if (!str_contains($cssContent, '@media (max-width: 640px)')) {
        $failures[] = '[media-query] responsive-table.css에 모바일 대응 media query(@media (max-width: 640px))가 포함되어야 한다.';
    }

    // (2-2) 태블릿/데스크톱 media query 확인 (min-width: 641px)
    if (!str_contains($cssContent, '@media (min-width: 641px)')) {
        $failures[] = '[media-query] responsive-table.css에 태블릿 이상 대응 media query(@media (min-width: 641px))가 포함되어야 한다.';
    }

    // (2-3) 사용자 설정(prefers) media query 확인
    if (!str_contains($cssContent, '@media (prefers-reduced-motion: reduce)')) {
        $failures[] = '[media-query] responsive-table.css에 감소된 모션 설정 media query가 포함되어야 한다.';
    }

    // (2-4) 다크모드 media query 확인
    if (!str_contains($cssContent, '@media (prefers-color-scheme: dark)')) {
        $failures[] = '[media-query] responsive-table.css에 다크모드 설정 media query가 포함되어야 한다.';
    }
}

// ============================================================================
// 3. design-tokens CSS의 media query 확인
// ============================================================================

$designTokensCssPath = __DIR__ . '/../../public/assets/css/design-tokens.css';

if (!is_file($designTokensCssPath)) {
    $failures[] = '[design-tokens] design-tokens.css 파일이 존재해야 한다.';
} else {
    $designTokensContent = file_get_contents($designTokensCssPath);

    // (3-1) 다크모드 media query
    if (!str_contains($designTokensContent, '@media (prefers-color-scheme: dark)')) {
        $failures[] = '[design-tokens] design-tokens.css에 다크모드 설정이 포함되어야 한다.';
    }

    // (3-2) 감소된 모션 media query
    if (!str_contains($designTokensContent, '@media (prefers-reduced-motion: reduce)')) {
        $failures[] = '[design-tokens] design-tokens.css에 감소된 모션 설정이 포함되어야 한다.';
    }
}

// ============================================================================
// 4. Print CSS의 media query 확인
// ============================================================================

$printCssPath = __DIR__ . '/../../public/assets/css/print.css';

if (!is_file($printCssPath)) {
    $failures[] = '[print-css] print.css 파일이 존재해야 한다.';
} else {
    $printCssContent = file_get_contents($printCssPath);

    // (4-1) print media query
    if (!str_contains($printCssContent, '@media print')) {
        $failures[] = '[print-css] print.css에 @media print가 포함되어야 한다.';
    }
}

// ============================================================================
// 5. HTML에 CSS 파일 링크 확인
// ============================================================================

// (5-1) design-tokens.css가 링크되어 있어야 한다.
if (!str_contains($html, '<link rel="stylesheet" href="/assets/css/design-tokens.css">')) {
    $failures[] = '[css-links] 레이아웃이 design-tokens.css를 링크해야 한다.';
}

// (5-2) print.css가 올바른 media 속성과 함께 링크되어야 한다.
if (!str_contains($html, '<link rel="stylesheet" href="/assets/css/print.css" media="print">')) {
    $failures[] = '[css-links] 레이아웃이 print.css를 media="print" 속성과 함께 링크해야 한다.';
}

// ============================================================================
// 결과 처리
// ============================================================================

if ($failures !== []) {
    fwrite(STDERR, "모바일 CSS 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "모바일 CSS 테스트 통과.\n");
exit(0);
