<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\FrontPage`의 동작을 확인하는 smoke test (태스크 0693).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 나무위키풍 대문이 (1) 검색 영역,
 * (2) 최근 편집된 문서 목록(있음/없음 두 상태), (3) 사이트 소개 블록을
 * 올바르게 렌더링하는지, 그리고 문서 제목이 XSS로부터 안전하게
 * escaping되는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Ui\FrontPage;

$failures = [];

// ============================================================================
// 1. 최근 문서가 없는 경우 — 빈 상태 안내를 보여줘야 한다.
// ============================================================================

$frontPage = new FrontPage();
$html = $frontPage->render([]);

if (!str_contains($html, '<h1 class="front-page__title">MintWiki</h1>')) {
    $failures[] = '대문이 브랜드 제목을 포함해야 한다.';
}
if (!str_contains($html, 'class="front-page__search"')) {
    $failures[] = '대문이 검색 영역을 포함해야 한다.';
}
if (!str_contains($html, '<form method="get" action="/api/documents/by-title"')) {
    $failures[] = '대문이 문서 검색 form을 포함해야 한다.';
}
if (!str_contains($html, 'class="front-page__recent"')) {
    $failures[] = '대문이 최근 편집된 문서 영역을 포함해야 한다.';
}
if (!str_contains($html, 'class="empty-state"')) {
    $failures[] = '최근 문서가 없으면 EmptyState 안내를 보여줘야 한다.';
}
if (str_contains($html, 'front-page__recent-list')) {
    $failures[] = '최근 문서가 없으면 목록을 렌더링하지 않아야 한다.';
}
if (!str_contains($html, 'class="front-page__about"')) {
    $failures[] = '대문이 사이트 소개 블록을 포함해야 한다.';
}

// ============================================================================
// 2. 최근 문서가 있는 경우 — 제목/링크가 담긴 목록을 보여줘야 한다.
// ============================================================================

$frontPage = new FrontPage();
$recentDocuments = [
    new Document('doc-1', '나무위키'),
    new Document('doc-2', '민트위키'),
];
$html = $frontPage->render($recentDocuments);

if (!str_contains($html, 'class="front-page__recent-list"')) {
    $failures[] = '최근 문서가 있으면 목록을 렌더링해야 한다.';
}
if (str_contains($html, 'class="empty-state"')) {
    $failures[] = '최근 문서가 있으면 빈 상태 안내를 보여주지 않아야 한다.';
}
if (!str_contains($html, '<a href="/wiki/' . rawurlencode('나무위키') . '">나무위키</a>')) {
    $failures[] = '최근 문서 목록이 문서 제목/링크를 포함해야 한다.';
}
if (!str_contains($html, '<a href="/wiki/' . rawurlencode('민트위키') . '">민트위키</a>')) {
    $failures[] = '최근 문서 목록이 두 번째 문서도 포함해야 한다.';
}

// ============================================================================
// 3. 문서 제목이 XSS로부터 안전하게 escaping되어야 한다.
// ============================================================================

$frontPage = new FrontPage();
$xssDocument = new Document('doc-xss', '<script>alert(1)</script>');
$html = $frontPage->render([$xssDocument]);

if (str_contains($html, '<script>alert(1)</script>')) {
    $failures[] = '최근 문서 제목이 escaping 없이 그대로 출력되면 안 된다.';
}
if (!str_contains($html, '&lt;script&gt;alert(1)&lt;/script&gt;')) {
    $failures[] = '최근 문서 제목이 escaping되어 표시되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "FrontPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FrontPage 테스트 통과.\n");
exit(0);
