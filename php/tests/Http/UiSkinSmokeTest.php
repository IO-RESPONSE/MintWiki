<?php

declare(strict_types=1);

/**
 * Phase H 스킨(태스크 0689-0694)이 실제 route 응답과 배포 자산에 통합되어
 * 있는지 확인하는 연기 테스트(태스크 0695). phpunit 없이 `php` CLI만으로
 * 실행되며, DB/자격 증명 없이 항상 실행할 수 있다(UiRoutesTest.php와 동일한
 * 방식) — 개별 컴포넌트 단위 테스트(NavigationBarTest.php,
 * DocumentActionTabsTest.php 등)와 달리, `public/index.php`가 등록하는
 * route 응답 HTML과 배포되는 CSS 파일 내용을 직접 확인한다.
 *
 * 확인 대상(0695 acceptance criteria):
 * (1) 상단바 노출: GET / 응답이 상단 네비게이션 바(site-nav)를 포함하는지.
 * (2) 브랜드색 #008485 적용: design-tokens.css가 --color-brand 토큰을
 *     #008485로 정의하는지.
 * (3) 문서 액션 탭: GET /wiki/{title} 응답이 document-tabs를 포함하는지.
 * (4) 반응형: sidebar.css가 좁은 화면을 위한 @media 규칙을 포함하는지.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\InMemoryRepository;
use MintWiki\Document\Service;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\FrontPage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;

$failures = [];
$cssDir = __DIR__ . '/../../public/assets/css';

// ============================================================================
// (1) 상단바 노출: GET / 응답이 상단 네비게이션 바를 포함해야 한다.
// ============================================================================

$headerContent = (new NavigationBar())->render(new Navigation(), '/', []);
$homeLayout = new Layout(null, $headerContent);

$router = new Router();
$router->register('GET', '/', static function () use ($homeLayout): Response {
    return Response::html((new FrontPage(null, $homeLayout))->render([]));
});

$homeHandler = $router->match(new Request('GET', '/'));
if ($homeHandler === null) {
    $failures[] = 'GET / route는 등록되어 있어야 한다.';
} else {
    $homeBody = $homeHandler()->body();

    if (!str_contains($homeBody, '<header><nav class="site-nav"')) {
        $failures[] = 'GET / 응답이 상단 네비게이션 바(site-nav)를 포함해야 한다(태스크 0690, 0691).';
    }
    if (!str_contains($homeBody, '<a class="site-nav__brand" href="/">MintWiki</a>')) {
        $failures[] = 'GET / 응답의 상단 네비게이션 바가 브랜드 로고를 포함해야 한다.';
    }
    foreach ([
        '/assets/css/navigation.css',
        '/assets/css/sidebar.css',
        '/assets/css/document-header.css',
        '/assets/css/front-page.css',
    ] as $stylesheet) {
        if (!str_contains($homeBody, '<link rel="stylesheet" href="' . $stylesheet . '">')) {
            $failures[] = "GET / 응답이 스킨 스타일시트({$stylesheet})를 포함해야 한다.";
        }
    }
}

// ============================================================================
// (2) 브랜드색 #008485 적용: design-tokens.css가 --color-brand를 정의해야 한다.
// ============================================================================

$designTokensPath = $cssDir . '/design-tokens.css';
if (!is_file($designTokensPath)) {
    $failures[] = 'design-tokens.css 파일이 존재해야 한다.';
} else {
    $designTokensCss = file_get_contents($designTokensPath);
    if (!str_contains($designTokensCss, '--color-brand: #008485;')) {
        $failures[] = 'design-tokens.css가 --color-brand를 #008485로 정의해야 한다(태스크 0689).';
    }
}

// ============================================================================
// (3) 문서 액션 탭: GET /wiki/{title} 응답이 document-tabs를 포함해야 한다.
// ============================================================================

$documentLayout = new Layout(null, $headerContent);
$repository = new InMemoryRepository();
$repository->create(new Document('doc-1', 'Skin Smoke Test Document'));

$documentRouter = new Router();
$documentRouter->register('GET', '/wiki/{title}', static function (array $params) use ($documentLayout, $repository): Response {
    $documentViewPage = new DocumentViewPage(null, $documentLayout);
    $requestedTitle = rawurldecode($params['title'] ?? '');
    $documentService = new Service($repository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html($documentViewPage->render(null, null, $requestedTitle), 404);
    }

    return Response::html($documentViewPage->render($document));
});

$documentHandler = $documentRouter->match(new Request('GET', '/wiki/Skin Smoke Test Document'));
if ($documentHandler === null) {
    $failures[] = 'GET /wiki/{title} route는 등록되어 있어야 한다.';
} else {
    $documentBody = $documentHandler()->body();

    if (!str_contains($documentBody, '<ul class="document-tabs">')) {
        $failures[] = 'GET /wiki/{title} 응답이 문서 액션 탭(document-tabs)을 포함해야 한다(태스크 0692).';
    }
    if (!str_contains($documentBody, '<header><nav class="site-nav"')) {
        $failures[] = 'GET /wiki/{title} 응답도 상단 네비게이션 바를 포함해야 한다.';
    }
}

// ============================================================================
// (4) 반응형: sidebar.css가 좁은 화면을 위한 @media 규칙을 포함해야 한다.
// ============================================================================

$sidebarCssPath = $cssDir . '/sidebar.css';
if (!is_file($sidebarCssPath)) {
    $failures[] = 'sidebar.css 파일이 존재해야 한다.';
} else {
    $sidebarCss = file_get_contents($sidebarCssPath);
    if (!str_contains($sidebarCss, '@media (max-width:')) {
        $failures[] = 'sidebar.css가 모바일 반응형 @media 규칙을 포함해야 한다(태스크 0694).';
    }
}

if ($failures !== []) {
    fwrite(STDERR, "스킨 통합 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "스킨 통합 연기 테스트 통과.\n");
exit(0);
