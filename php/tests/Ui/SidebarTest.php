<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\Sidebar`의 동작을 확인하는 smoke test (태스크 0694).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 나무위키식 사이드바/도구 영역이
 * "최근 변경", "랜덤 문서", "문서 검색" 링크를 노출하는지, <details>/<summary>
 * 네이티브 토글 구조로 렌더링되는지, aria-label을 포함하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Sidebar;

$failures = [];

$sidebar = new Sidebar();
$html = $sidebar->render();

// (1) aside landmark와 aria-label을 포함해야 한다.
if (!str_contains($html, '<aside class="site-sidebar" aria-label="도구">')) {
    $failures[] = '[구조] aside class="site-sidebar" aria-label="도구"로 시작해야 한다.';
}

// (2) <details>/<summary> 토글 구조여야 한다(JS 없이 접힘/펼침).
if (!str_contains($html, '<details class="site-sidebar__toggle">')) {
    $failures[] = '[구조] <details class="site-sidebar__toggle">를 포함해야 한다.';
}

if (!str_contains($html, '<summary class="site-sidebar__summary">도구</summary>')) {
    $failures[] = '[구조] <summary>가 "도구" 텍스트를 표시해야 한다.';
}

// (3) 최소 링크(최근 변경/랜덤 문서/문서 검색)가 노출되어야 한다.
foreach ([
    '최근 변경' => '/recent-changes',
    '랜덤 문서' => '/random',
    '문서 검색' => '/search',
] as $label => $expectedHref) {
    if (!str_contains($html, 'href="' . $expectedHref . '">' . $label . '</a>')) {
        $failures[] = "[링크] \"{$label}\" 링크가 {$expectedHref}로 노출되어야 한다.";
    }
}

// (4) 링크는 <ul class="site-sidebar__menu"> 안에 있어야 한다.
if (!str_contains($html, '<ul class="site-sidebar__menu">')) {
    $failures[] = '[구조] 링크가 <ul class="site-sidebar__menu">로 감싸져야 한다.';
}

if (!str_contains($html, 'class="site-sidebar__link"')) {
    $failures[] = '[구조] 각 링크가 site-sidebar__link class를 가져야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Sidebar 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Sidebar 테스트 통과.\n");
exit(0);
