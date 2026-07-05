<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\Layout의 최소 HTML skeleton 렌더링을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Layout;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\NavigationItem;
use MintWiki\Ui\SeoMetadata;
use MintWiki\User\User;

$failures = [];
$layout = new Layout();

$html = $layout->render('MintWiki <Home>', '<main><h1>홈</h1></main>');

foreach ([
    '<!doctype html>' => 'doctype을 포함해야 한다.',
    '<html lang="ko">' => '기본 lang은 ko여야 한다.',
    '<meta charset="utf-8">' => 'UTF-8 meta charset을 포함해야 한다.',
    '<meta name="viewport" content="width=device-width, initial-scale=1">' => 'viewport meta를 포함해야 한다.',
    '<title>MintWiki &lt;Home&gt;</title>' => 'title은 escape해야 한다.',
    '<link rel="stylesheet" href="/assets/css/design-tokens.css">' => 'design-tokens CSS를 포함해야 한다.',
    '<link rel="stylesheet" href="/assets/css/navigation.css">' => 'navigation CSS를 포함해야 한다.',
    '<link rel="stylesheet" href="/assets/css/layout.css">' => 'layout CSS를 포함해야 한다.',
    '<link rel="stylesheet" href="/assets/css/buttons.css">' => 'buttons CSS를 포함해야 한다.',
    '<link rel="stylesheet" href="/assets/css/print.css" media="print">' => 'print CSS를 포함해야 한다.',
    '<header></header>' => 'header에 navigation을 전달하지 않으면 기존과 같이 비어있어야 한다(하위 호환).',
    '<div class="site-content"><main><h1>홈</h1></main></div>' => 'body는 --content-max-width 폭 wrapper 안에 포함되어야 한다.',
    '<footer>' => 'footer landmark를 포함해야 한다.',
    '<div class="site-footer-info">' => 'footer가 나무위키풍 사이트 정보 블록을 포함해야 한다.',
    '<p class="site-footer-info__name">MintWiki</p>' => 'footer가 사이트 이름을 표시해야 한다.',
] as $needle => $message) {
    if (!str_contains($html, $needle)) {
        $failures[] = $message;
    }
}

if (!preg_match('/site-footer-info__license">[^<]+라이선스[^<]*</', $html)) {
    $failures[] = 'footer가 라이선스/이용 안내 문구를 포함해야 한다.';
}

// header에 navigation을 전달하면 상단 네비게이션 바가 header 안에 렌더링된다 (태스크 0691).
$navigation = new Navigation([new NavigationItem('/wiki/Home', '홈', '/wiki/Home')]);
$user = new User('user-1', 'alice', '앨리스');
$headerContent = (new NavigationBar())->render($navigation, '/wiki/Home', [], $user);
$layoutWithNav = new Layout(null, $headerContent);
$htmlWithNav = $layoutWithNav->render('MintWiki', '<main>본문</main>');

if (!str_contains($htmlWithNav, '<header><nav class="site-nav"')) {
    $failures[] = 'header에 navigation을 전달하면 <nav class="site-nav">가 header 안에 렌더링되어야 한다.';
}

if (!str_contains($htmlWithNav, '로그아웃(alice)')) {
    $failures[] = 'header에 전달한 NavigationBar의 로그인 상태가 그대로 렌더링되어야 한다.';
}

// 사이드바(0694)는 별도 전달 없이도 기본으로 렌더링되어야 한다.
if (!str_contains($html, '<div class="site-layout"><div class="site-content">')) {
    $failures[] = 'body는 site-layout 안의 site-content wrapper 안에 포함되어야 한다(태스크 0694).';
}

if (!str_contains($html, '<aside class="site-sidebar" aria-label="도구">')) {
    $failures[] = '기본 Layout이 사이드바(aside.site-sidebar)를 렌더링해야 한다(태스크 0694).';
}

if (!str_contains($html, 'href="/recent-changes">최근 변경</a>')) {
    $failures[] = '사이드바에 "최근 변경" 링크가 노출되어야 한다(태스크 0694).';
}

if (!str_contains($html, '<link rel="stylesheet" href="/assets/css/sidebar.css">')) {
    $failures[] = 'sidebar CSS를 포함해야 한다(태스크 0694).';
}

// sidebarContent를 명시적으로 전달하면 그 내용이 그대로 렌더링되어야 한다.
$customSidebarLayout = new Layout(null, null, '<aside class="custom-sidebar">커스텀</aside>');
$customSidebarHtml = $customSidebarLayout->render('MintWiki', '<main>본문</main>');
if (!str_contains($customSidebarHtml, '<aside class="custom-sidebar">커스텀</aside>')) {
    $failures[] = 'sidebarContent를 명시적으로 전달하면 그 내용이 그대로 렌더링되어야 한다(태스크 0694).';
}

if (str_contains($customSidebarHtml, 'site-sidebar')) {
    $failures[] = 'sidebarContent를 명시적으로 전달하면 기본 Sidebar는 렌더링되면 안 된다(태스크 0694).';
}

// 다른 Layout 인스턴스(navigation 미전달)는 여전히 header가 비어있어야 한다(인스턴스 간 격리 확인).
$plainHtmlAfterNavUsage = $layout->render('MintWiki', '<main>본문</main>');
if (!str_contains($plainHtmlAfterNavUsage, '<header></header>')) {
    $failures[] = 'navigation을 생성자에 전달하지 않은 Layout 인스턴스는 header가 비어있어야 한다.';
}

$langHtml = $layout->render('Title', '<p>body</p>', 'ko" data-x="1');
if (!str_contains($langHtml, '<html lang="ko&quot; data-x=&quot;1">')) {
    $failures[] = 'lang attribute는 escape해야 한다.';
}

// requestId 테스트
$requestIdHtml = $layout->render('Title', '<p>body</p>', 'ko', 'req-12345');
if (!str_contains($requestIdHtml, 'data-request-id="req-12345"')) {
    $failures[] = 'data-request-id attribute를 포함해야 한다.';
}

if (!str_contains($requestIdHtml, '요청ID: req-12345')) {
    $failures[] = 'footer에 요청ID 텍스트를 포함해야 한다.';
}

// requestId XSS 테스트
$requestIdXssHtml = $layout->render('Title', '<p>body</p>', 'ko', '<script>alert("xss")</script>');
if (str_contains($requestIdXssHtml, '<script>')) {
    $failures[] = 'requestId의 script 태그는 escape되어야 한다.';
}

if (!str_contains($requestIdXssHtml, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')) {
    $failures[] = 'requestId이 escape되어야 한다.';
}

// requestId가 null일 때 footer가 비어있어야 함
$noRequestIdHtml = $layout->render('Title', '<p>body</p>', 'ko', null);
if (str_contains($noRequestIdHtml, 'data-request-id')) {
    $failures[] = 'requestId가 null일 때 data-request-id attribute를 포함하면 안 된다.';
}

if (str_contains($noRequestIdHtml, '요청ID:')) {
    $failures[] = 'requestId가 null일 때 "요청ID:" 텍스트를 포함하면 안 된다.';
}

if (!str_contains($noRequestIdHtml, '<footer>')) {
    $failures[] = 'requestId가 null일 때에도 footer landmark를 포함해야 한다.';
}

// SEO 메타데이터 테스트
$seo = new SeoMetadata('문서 제목', '이것은 문서 설명입니다.', '/docs/test-doc');
$seoHtml = $layout->render('문서 제목', '<p>body</p>', 'ko', null, $seo);

if (!str_contains($seoHtml, '<meta name="description" content="이것은 문서 설명입니다.">')) {
    $failures[] = 'SEO 메타데이터의 description을 포함해야 한다.';
}

if (!str_contains($seoHtml, '<link rel="canonical" href="/docs/test-doc">')) {
    $failures[] = 'SEO 메타데이터의 canonical link를 포함해야 한다.';
}

// SEO description escape 테스트
$seoEscapeHtml = $layout->render('Title', '<p>body</p>', 'ko', null, new SeoMetadata('Title', '설명 "따옴표" <test>', null));
if (!str_contains($seoEscapeHtml, 'content="설명 &quot;따옴표&quot; &lt;test&gt;"')) {
    $failures[] = 'SEO description의 속성값이 escape되어야 한다.';
}

// SEO canonical 링크 escape 테스트
$seoCanonicalEscapeHtml = $layout->render('Title', '<p>body</p>', 'ko', null, new SeoMetadata('Title', null, '/docs/test?param="xss"'));
if (!str_contains($seoCanonicalEscapeHtml, 'href="/docs/test?param=&quot;xss&quot;"')) {
    $failures[] = 'SEO canonical URL의 속성값이 escape되어야 한다.';
}

// SEO 없을 때 테스트 (backward compatibility)
$noSeoHtml = $layout->render('Title', '<p>body</p>', 'ko', null, null);
if (str_contains($noSeoHtml, 'name="description"')) {
    $failures[] = 'SEO가 없을 때 description 메타 태그를 포함하면 안 된다.';
}

if (str_contains($noSeoHtml, 'rel="canonical"')) {
    $failures[] = 'SEO가 없을 때 canonical 링크를 포함하면 안 된다.';
}

// SEO 부분 설정 테스트: description만 있는 경우
$partialSeoHtml = $layout->render('Title', '<p>body</p>', 'ko', null, new SeoMetadata('Title', '설명만 있음', null));
if (!str_contains($partialSeoHtml, '<meta name="description" content="설명만 있음">')) {
    $failures[] = 'SEO description만 있을 때 description 메타 태그를 포함해야 한다.';
}

if (str_contains($partialSeoHtml, 'rel="canonical"')) {
    $failures[] = 'SEO canonical이 없을 때 canonical 링크를 포함하면 안 된다.';
}

// SEO 부분 설정 테스트: canonical만 있는 경우
$partialSeo2Html = $layout->render('Title', '<p>body</p>', 'ko', null, new SeoMetadata('Title', null, '/docs/test'));
if (str_contains($partialSeo2Html, 'name="description"')) {
    $failures[] = 'SEO description이 없을 때 description 메타 태그를 포함하면 안 된다.';
}

if (!str_contains($partialSeo2Html, '<link rel="canonical" href="/docs/test">')) {
    $failures[] = 'SEO canonical만 있을 때 canonical 링크를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Layout 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Layout 테스트 통과.\n");
exit(0);
