<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentActionTabs`의 동작을 확인하는 smoke test (태스크 0692).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 나무위키식 문서 액션 탭(읽기/편집/
 * 역사/토론)이 올바른 `/wiki/{title}` 경로로 링크되는지, 현재 경로와 일치하는
 * 탭만 활성 표시되는지, 제목이 URL 인코딩되는지, 사용자 입력이 escaping되어
 * XSS를 방지하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\DocumentActionTabs;

$failures = [];

$actionTabs = new DocumentActionTabs();

// (1) 네 탭 모두 올바른 /wiki/{title} 경로로 링크되어야 한다.
$html = $actionTabs->render('테스트 문서');

if (!str_contains($html, '<ul class="document-tabs">')) {
    $failures[] = '[구조] <ul class="document-tabs">로 시작해야 한다.';
}

$encodedTitle = rawurlencode('테스트 문서');

foreach ([
    '읽기' => '/wiki/' . $encodedTitle,
    '편집' => '/wiki/' . $encodedTitle . '/edit',
    '역사' => '/wiki/' . $encodedTitle . '/history',
    '토론' => '/wiki/' . $encodedTitle . '/discussion',
] as $label => $expectedHref) {
    if (!str_contains($html, 'href="' . $expectedHref . '">' . $label . '</a>')) {
        $failures[] = "[탭] \"{$label}\" 탭이 {$expectedHref}로 링크되어야 한다.";
    }
}

// (2) currentPath와 일치하는 탭만 active class/aria-current를 가진다.
$activeHtml = $actionTabs->render('테스트 문서', '/wiki/' . $encodedTitle . '/edit');

if (!str_contains(
    $activeHtml,
    'class="document-tabs__link document-tabs__link--active" href="/wiki/' . $encodedTitle . '/edit" aria-current="page">편집'
)) {
    $failures[] = '[활성] 현재 경로가 편집 탭과 일치하면 편집 탭이 active로 표시되어야 한다.';
}

if (str_contains($activeHtml, 'document-tabs__link--active" href="/wiki/' . $encodedTitle . '" aria-current')) {
    $failures[] = '[활성] 편집 경로에서는 읽기 탭이 active로 표시되면 안 된다.';
}

// (3) currentPath를 생략하면 어떤 탭도 active로 표시되지 않는다.
$noActiveHtml = $actionTabs->render('테스트 문서');

if (str_contains($noActiveHtml, 'document-tabs__link--active')) {
    $failures[] = '[활성] currentPath가 없으면 어떤 탭도 active로 표시되면 안 된다.';
}

// (4) 제목에 공백/특수문자가 있어도 URL 인코딩되어 링크에 반영된다.
$spacedHtml = $actionTabs->render('띄어 쓰기 문서');
if (!str_contains($spacedHtml, 'href="/wiki/' . rawurlencode('띄어 쓰기 문서') . '"')) {
    $failures[] = '[인코딩] 제목의 공백이 URL 인코딩되어야 한다.';
}

// (5) XSS 방지: 제목에 포함된 특수문자는 escape되어야 한다.
$xssTitle = '<script>alert(1)</script>';
$xssHtml = $actionTabs->render($xssTitle);

if (str_contains($xssHtml, '<script>alert(1)</script>')) {
    $failures[] = '[XSS] 제목이 escape되지 않고 링크에 그대로 출력되었다.';
}

if (!str_contains($xssHtml, rawurlencode($xssTitle))) {
    $failures[] = '[XSS] 제목이 URL 인코딩되어 href에 반영되어야 한다.';
}

// (6) 삭제 탭(태스크 0715): canDelete가 false(기본값)면 삭제 탭이 노출되지 않는다.
$noDeleteHtml = $actionTabs->render('테스트 문서');
if (str_contains($noDeleteHtml, '/delete">삭제</a>')) {
    $failures[] = '[삭제] canDelete를 지정하지 않으면 삭제 탭이 노출되면 안 된다.';
}

$explicitNoDeleteHtml = $actionTabs->render('테스트 문서', '', false);
if (str_contains($explicitNoDeleteHtml, '/delete">삭제</a>')) {
    $failures[] = '[삭제] canDelete=false면 삭제 탭이 노출되면 안 된다.';
}

// (7) 삭제 탭: canDelete가 true면 /wiki/{title}/delete로 링크되는 삭제 탭이 노출된다.
$withDeleteHtml = $actionTabs->render('테스트 문서', '', true);
if (!str_contains($withDeleteHtml, 'href="/wiki/' . $encodedTitle . '/delete">삭제</a>')) {
    $failures[] = '[삭제] canDelete=true면 삭제 탭이 /wiki/{title}/delete로 링크되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentActionTabs 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentActionTabs 테스트 통과.\n");
exit(0);
