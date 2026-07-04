<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\NavigationBar`의 동작을 확인하는 smoke test (태스크 0690).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 나무위키풍 상단바가 브랜드 로고,
 * 검색 입력, navigation 항목, 로그인/로그아웃 상태를 올바르게 렌더링하는지,
 * 활성 항목/권한 필터링이 `Navigation` API 결과와 일치하는지, 사용자 입력이
 * escaping되어 XSS를 방지하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\NavigationItem;
use MintWiki\User\User;

$failures = [];

$navigation = new Navigation([
    new NavigationItem('/home', '홈', '/home'),
    new NavigationItem('/admin', '관리', '/admin', 'admin:read'),
]);

// (1) 비로그인 상태: 브랜드 로고, 검색 입력, 로그인 링크가 렌더링된다.
$navBar = new NavigationBar();
$html = $navBar->render($navigation, '/home', []);

if (!str_contains($html, '<nav class="site-nav"')) {
    $failures[] = '[구조] <nav class="site-nav">로 시작해야 한다.';
}

if (!str_contains($html, '<a class="site-nav__brand" href="/">MintWiki</a>')) {
    $failures[] = '[브랜드] 브랜드 로고 "MintWiki"가 "/"로 링크되어야 한다.';
}

if (!str_contains($html, '<form class="site-nav__search" action="/search" method="get"')) {
    $failures[] = '[검색] 검색 폼이 /search로 제출되어야 한다.';
}

if (!str_contains($html, 'name="q"')) {
    $failures[] = '[검색] 검색 입력의 name은 "q"여야 한다.';
}

if (!str_contains($html, '<a class="site-nav__auth-link" href="/login">로그인</a>')) {
    $failures[] = '[인증] 비로그인 상태에서는 "로그인" 링크가 표시되어야 한다.';
}

if (str_contains($html, '로그아웃')) {
    $failures[] = '[인증] 비로그인 상태에서는 "로그아웃"이 표시되면 안 된다.';
}

// (2) 권한 필터링: admin:read 권한이 없으면 "관리" 항목이 보이지 않는다.
if (str_contains($html, '>관리<')) {
    $failures[] = '[권한] 권한이 없는 사용자에게는 "관리" 항목이 보이면 안 된다.';
}

if (!str_contains($html, '>홈<')) {
    $failures[] = '[권한] 권한이 필요 없는 "홈" 항목은 항상 보여야 한다.';
}

// (3) 활성 항목: 현재 경로와 일치하는 항목에 active class와 aria-current가 붙는다.
if (!str_contains($html, 'class="site-nav__link site-nav__link--active" href="/home" aria-current="page"')) {
    $failures[] = '[활성] 현재 경로와 일치하는 항목은 active class와 aria-current="page"를 가져야 한다.';
}

// (4) 로그인 상태 + 권한 있음: "관리" 항목이 보이고 로그아웃(사용자명)이 표시된다.
$user = new User('user-1', 'alice', '앨리스');
$navBarLoggedIn = new NavigationBar();
$htmlLoggedIn = $navBarLoggedIn->render($navigation, '/admin', ['admin:read'], $user);

if (!str_contains($htmlLoggedIn, '>관리<')) {
    $failures[] = '[권한] admin:read 권한이 있으면 "관리" 항목이 보여야 한다.';
}

if (!str_contains($htmlLoggedIn, '<a class="site-nav__auth-link" href="/logout">로그아웃(alice)</a>')) {
    $failures[] = '[인증] 로그인 상태에서는 "로그아웃(사용자명)" 링크가 표시되어야 한다.';
}

if (str_contains($htmlLoggedIn, '>로그인<')) {
    $failures[] = '[인증] 로그인 상태에서는 "로그인" 링크가 표시되면 안 된다.';
}

if (!str_contains($htmlLoggedIn, 'class="site-nav__link site-nav__link--active" href="/admin" aria-current="page"')) {
    $failures[] = '[활성] /admin 경로에서는 "관리" 항목이 active로 표시되어야 한다.';
}

// (5) XSS 방지: 사용자명과 navigation label에 포함된 특수문자가 escape된다.
$xssUser = new User('user-2', '<script>alert(1)</script>');
$navBarXss = new NavigationBar();
$htmlXss = $navBarXss->render($navigation, '/home', [], $xssUser);

if (str_contains($htmlXss, '<script>alert(1)</script>')) {
    $failures[] = '[XSS] 사용자명이 escape되지 않고 그대로 출력되었다.';
}

if (!str_contains($htmlXss, '&lt;script&gt;alert(1)&lt;/script&gt;')) {
    $failures[] = '[XSS] 사용자명이 올바르게 escape되어야 한다.';
}

$navigationWithXssItem = new Navigation([
    new NavigationItem('/x?a=1&b=2', '<b>홈</b>"', '/x?a=1&b=2'),
]);
$navBarXssItem = new NavigationBar();
$htmlXssItem = $navBarXssItem->render($navigationWithXssItem, '/x?a=1&b=2', []);

if (str_contains($htmlXssItem, '<b>홈</b>')) {
    $failures[] = '[XSS] navigation 항목 label이 escape되지 않고 그대로 출력되었다.';
}

if (!str_contains($htmlXssItem, '&lt;b&gt;홈&lt;/b&gt;&quot;')) {
    $failures[] = '[XSS] navigation 항목 label이 올바르게 escape되어야 한다.';
}

if (!str_contains($htmlXssItem, 'href="/x?a=1&amp;b=2"')) {
    $failures[] = '[XSS] navigation 항목 href의 "&"가 escape되어야 한다.';
}

// (6) navigation 항목이 없어도 오류 없이 렌더링된다.
$emptyNavigation = new Navigation();
$navBarEmpty = new NavigationBar();
$htmlEmpty = $navBarEmpty->render($emptyNavigation, '/anything', []);

if (!str_contains($htmlEmpty, '<a class="site-nav__brand" href="/">MintWiki</a>')) {
    $failures[] = '[빈 메뉴] navigation 항목이 없어도 브랜드 로고는 렌더링되어야 한다.';
}

if (str_contains($htmlEmpty, '<ul class="site-nav__menu">')) {
    $failures[] = '[빈 메뉴] navigation 항목이 없으면 메뉴 목록을 렌더링하면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "NavigationBar 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "NavigationBar 테스트 통과.\n");
exit(0);
