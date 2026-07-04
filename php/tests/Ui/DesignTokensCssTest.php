<?php

declare(strict_types=1);

/**
 * MintWiki 브랜드 색 토큰과 나무위키풍 레이아웃 토큰을 확인하는 테스트 (태스크 0689).
 *
 * design-tokens.css에 브랜드 색(#008485)과 관련 hover/active/on-brand 토큰,
 * 링크/방문 링크색, 콘텐츠 최대 폭, 헤더 높이 토큰이 정의되어 있는지 검증한다.
 * buttons.css의 주요(submit) 버튼이 하드코딩 색이 아닌 브랜드 토큰을
 * 사용하는지도 함께 확인한다.
 */

$failures = [];

// ============================================================================
// 1. design-tokens.css의 브랜드 색 토큰 확인
// ============================================================================

$designTokensCssPath = __DIR__ . '/../../public/assets/css/design-tokens.css';

if (!is_file($designTokensCssPath)) {
    $failures[] = '[design-tokens] design-tokens.css 파일이 존재해야 한다.';
} else {
    $designTokensContent = file_get_contents($designTokensCssPath);

    // (1-1) 브랜드 색 토큰과 실제 값(#008485)이 존재해야 한다.
    if (!str_contains($designTokensContent, '--color-brand')) {
        $failures[] = '[brand] design-tokens.css에 --color-brand 토큰이 정의되어야 한다.';
    }

    if (!str_contains($designTokensContent, '#008485')) {
        $failures[] = '[brand] design-tokens.css에 브랜드 색 값 #008485가 포함되어야 한다.';
    }

    // (1-2) hover/active 명암 변형 토큰이 존재해야 한다.
    if (!str_contains($designTokensContent, '--color-brand-hover')) {
        $failures[] = '[brand] design-tokens.css에 --color-brand-hover 토큰이 정의되어야 한다.';
    }

    if (!str_contains($designTokensContent, '--color-brand-active')) {
        $failures[] = '[brand] design-tokens.css에 --color-brand-active 토큰이 정의되어야 한다.';
    }

    // (1-3) 대비를 만족하는 on-brand 텍스트색 토큰이 존재해야 한다.
    if (!str_contains($designTokensContent, '--color-on-brand')) {
        $failures[] = '[brand] design-tokens.css에 --color-on-brand 토큰이 정의되어야 한다.';
    }

    // (1-4) 나무위키풍 링크/방문색 토큰이 존재해야 한다.
    if (!str_contains($designTokensContent, '--color-link:')) {
        $failures[] = '[layout] design-tokens.css에 --color-link 토큰이 정의되어야 한다.';
    }

    if (!str_contains($designTokensContent, '--color-link-visited')) {
        $failures[] = '[layout] design-tokens.css에 --color-link-visited 토큰이 정의되어야 한다.';
    }

    // (1-5) 콘텐츠 최대 폭과 헤더 높이 레이아웃 토큰이 존재해야 한다.
    if (!str_contains($designTokensContent, '--content-max-width')) {
        $failures[] = '[layout] design-tokens.css에 --content-max-width 토큰이 정의되어야 한다.';
    }

    if (!str_contains($designTokensContent, '--header-height')) {
        $failures[] = '[layout] design-tokens.css에 --header-height 토큰이 정의되어야 한다.';
    }

    // (1-6) 기존 토큰(--color-bg-*, --color-text-*)이 유지되어야 한다.
    if (!str_contains($designTokensContent, '--color-bg-primary')) {
        $failures[] = '[regression] design-tokens.css에 기존 --color-bg-primary 토큰이 유지되어야 한다.';
    }

    if (!str_contains($designTokensContent, '--color-text-primary')) {
        $failures[] = '[regression] design-tokens.css에 기존 --color-text-primary 토큰이 유지되어야 한다.';
    }
}

// ============================================================================
// 2. buttons.css가 브랜드 토큰을 사용하는지 확인
// ============================================================================

$buttonsCssPath = __DIR__ . '/../../public/assets/css/buttons.css';

if (!is_file($buttonsCssPath)) {
    $failures[] = '[buttons-css] buttons.css 파일이 존재해야 한다.';
} else {
    $buttonsCssContent = file_get_contents($buttonsCssPath);

    // (2-1) 주요(submit) 버튼이 브랜드 배경색 토큰을 사용해야 한다.
    if (!str_contains($buttonsCssContent, 'var(--color-brand)')) {
        $failures[] = '[buttons-css] buttons.css의 주요 버튼이 var(--color-brand)를 사용해야 한다.';
    }

    // (2-2) 주요 버튼의 텍스트색은 on-brand 토큰을 사용해야 한다.
    if (!str_contains($buttonsCssContent, 'var(--color-on-brand)')) {
        $failures[] = '[buttons-css] buttons.css의 주요 버튼이 var(--color-on-brand)를 사용해야 한다.';
    }

    // (2-3) hover/active 상태가 브랜드 명암 변형 토큰을 사용해야 한다.
    if (!str_contains($buttonsCssContent, 'var(--color-brand-hover)')) {
        $failures[] = '[buttons-css] buttons.css의 주요 버튼 hover가 var(--color-brand-hover)를 사용해야 한다.';
    }

    if (!str_contains($buttonsCssContent, 'var(--color-brand-active)')) {
        $failures[] = '[buttons-css] buttons.css의 주요 버튼 active가 var(--color-brand-active)를 사용해야 한다.';
    }
}

// ============================================================================
// 결과 처리
// ============================================================================

if ($failures !== []) {
    fwrite(STDERR, "design-tokens/buttons CSS 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "design-tokens/buttons CSS 테스트 통과.\n");
exit(0);
