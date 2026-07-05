<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentHeader`의 동작을 확인하는 smoke test (태스크 0692).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 제목(H1) + 액션 탭 + "마지막 편집"
 * 메타 정보가 올바르게 렌더링되는지, h1 태그 자체는 속성 없이 유지되는지
 * (기존 DocumentViewPage 테스트와의 하위 호환), 사용자 입력이 escaping되어
 * XSS를 방지하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\DocumentHeader;

$failures = [];

$header = new DocumentHeader();

// (1) 제목은 속성 없는 <h1>로, 탭 목록도 함께 렌더링되어야 한다.
$html = $header->render('테스트 문서');

if (!str_contains($html, '<h1>테스트 문서</h1>')) {
    $failures[] = '[구조] h1은 속성 없이 제목을 그대로 표시해야 한다.';
}

if (!str_contains($html, '<ul class="document-tabs">')) {
    $failures[] = '[구조] 액션 탭 목록이 함께 렌더링되어야 한다.';
}

if (str_contains($html, 'document-header__meta')) {
    $failures[] = '[메타] lastEditedBy가 없으면 메타 정보를 렌더링하면 안 된다.';
}

// (2) lastEditedBy가 주어지면 "마지막 편집" 메타 정보를 표시한다.
$htmlWithMeta = $header->render('테스트 문서', '', 'alice');

if (!str_contains($htmlWithMeta, '<p class="document-header__meta">마지막 편집: alice</p>')) {
    $failures[] = '[메타] lastEditedBy가 주어지면 "마지막 편집" 메타 정보를 표시해야 한다.';
}

// (3) lastEditedBy가 빈 문자열/공백만 있으면 메타 정보를 생략한다.
$htmlWithBlankMeta = $header->render('테스트 문서', '', '   ');

if (str_contains($htmlWithBlankMeta, 'document-header__meta')) {
    $failures[] = '[메타] lastEditedBy가 공백만 있으면 메타 정보를 생략해야 한다.';
}

// (4) currentPath가 탭 중 하나와 일치하면 그 탭이 active로 표시된다.
$encodedTitle = rawurlencode('테스트 문서');
$activeHtml = $header->render('테스트 문서', '/wiki/' . $encodedTitle . '/history');

if (!str_contains($activeHtml, 'document-tabs__link--active" href="/wiki/' . $encodedTitle . '/history"')) {
    $failures[] = '[활성] currentPath와 일치하는 탭이 active로 표시되어야 한다.';
}

// (5) XSS 방지: 제목과 lastEditedBy 모두 escape되어야 한다.
$xssHtml = $header->render('<script>alert(1)</script>', '', '<b>bob</b>');

if (str_contains($xssHtml, '<script>alert(1)</script>')) {
    $failures[] = '[XSS] 제목이 escape되지 않고 그대로 출력되었다.';
}

if (!str_contains($xssHtml, '<h1>&lt;script&gt;alert(1)&lt;/script&gt;</h1>')) {
    $failures[] = '[XSS] 제목이 h1 안에서 올바르게 escape되어야 한다.';
}

if (str_contains($xssHtml, '<b>bob</b>')) {
    $failures[] = '[XSS] lastEditedBy가 escape되지 않고 그대로 출력되었다.';
}

if (!str_contains($xssHtml, '&lt;b&gt;bob&lt;/b&gt;')) {
    $failures[] = '[XSS] lastEditedBy가 올바르게 escape되어야 한다.';
}

// (6) 삭제 탭(태스크 0715): canDelete를 지정하지 않으면(기본값 false) 삭제
// 탭이 노출되지 않고, true면 노출된다.
$noDeleteHtml = $header->render('테스트 문서');
if (str_contains($noDeleteHtml, '/delete">삭제</a>')) {
    $failures[] = '[삭제] canDelete를 지정하지 않으면 삭제 탭이 노출되면 안 된다.';
}

$withDeleteHtml = $header->render('테스트 문서', '', null, true);
if (!str_contains($withDeleteHtml, 'href="/wiki/' . $encodedTitle . '/delete">삭제</a>')) {
    $failures[] = '[삭제] canDelete=true면 삭제 탭이 /wiki/{title}/delete로 링크되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentHeader 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentHeader 테스트 통과.\n");
exit(0);
