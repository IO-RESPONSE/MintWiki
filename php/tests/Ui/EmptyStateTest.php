<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\EmptyState`의 동작을 확인하는 smoke test (태스크 0553).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 빈 상태 컴포넌트가 올바르게
 * 렌더링되는지 확인한다. title/description/action 구조가 올바르게
 * 동작해야 한다. 모든 텍스트와 URL은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\EmptyState;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 empty state 생성
$escaper = new Escaper();
$emptyState = new EmptyState($escaper);

// (1) 제목이 빈 문자열일 때 빈 문자열 반환
$html = $emptyState->render('', null, null);

if ($html !== '') {
    $failures[] = '제목이 빈 문자열이면 빈 문자열을 반환해야 한다.';
}

// (2) 제목만 있을 때 렌더링
$html = $emptyState->render('문서가 없습니다');

if (!str_contains($html, '<div class="empty-state">')) {
    $failures[] = '빈 상태 컨테이너가 있어야 한다.';
}

if (!str_contains($html, '<div class="empty-state__content">')) {
    $failures[] = '빈 상태 콘텐츠 컨테이너가 있어야 한다.';
}

if (!str_contains($html, '<h2 class="empty-state__title">문서가 없습니다</h2>')) {
    $failures[] = '제목이 h2 요소로 렌더링되어야 한다.';
}

if (!str_contains($html, '</div>')) {
    $failures[] = '닫는 div 태그가 있어야 한다.';
}

// (3) 제목과 설명
$html = $emptyState->render('문서가 없습니다', '문서를 추가하려면 아래 버튼을 클릭하세요.');

if (!str_contains($html, '<p class="empty-state__description">문서를 추가하려면 아래 버튼을 클릭하세요.</p>')) {
    $failures[] = '설명이 p 요소로 렌더링되어야 한다.';
}

// (4) 설명이 null일 때
$html = $emptyState->render('문서가 없습니다', null);

if (str_contains($html, 'empty-state__description')) {
    $failures[] = '설명이 null이면 description 요소가 없어야 한다.';
}

// (5) 설명이 빈 문자열일 때
$html = $emptyState->render('문서가 없습니다', '');

if (str_contains($html, 'empty-state__description')) {
    $failures[] = '설명이 빈 문자열이면 description 요소가 없어야 한다.';
}

// (6) 제목, 설명, 액션 모두 포함
$html = $emptyState->render(
    '검색 결과가 없습니다',
    '다른 검색어를 시도해주세요.',
    ['href' => '/search', 'label' => '검색하기']
);

if (!str_contains($html, '<a href="/search" class="empty-state__action">검색하기</a>')) {
    $failures[] = '액션 버튼이 a 요소로 렌더링되어야 한다.';
}

// (7) 액션이 null일 때
$html = $emptyState->render('문서가 없습니다', '문서를 만들어보세요.', null);

if (str_contains($html, 'empty-state__action')) {
    $failures[] = '액션이 null이면 action 요소가 없어야 한다.';
}

// (8) 액션이 배열이지만 href가 없을 때
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['label' => '생성']
);

if (str_contains($html, 'empty-state__action')) {
    $failures[] = 'href가 없으면 action 요소가 렌더링되지 않아야 한다.';
}

// (9) 액션이 배열이지만 label이 없을 때
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['href' => '/documents/create']
);

if (str_contains($html, 'empty-state__action')) {
    $failures[] = 'label이 없으면 action 요소가 렌더링되지 않아야 한다.';
}

// (10) 액션 href가 빈 문자열일 때
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['href' => '', 'label' => '생성']
);

if (str_contains($html, 'empty-state__action')) {
    $failures[] = 'href가 빈 문자열이면 action 요소가 렌더링되지 않아야 한다.';
}

// (11) 액션 label이 빈 문자열일 때
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['href' => '/documents/create', 'label' => '']
);

if (str_contains($html, 'empty-state__action')) {
    $failures[] = 'label이 빈 문자열이면 action 요소가 렌더링되지 않아야 한다.';
}

// (12) XSS 공격으로부터 보호 - 제목 escape
$html = $emptyState->render('<script>alert("xss")</script>');

if (str_contains($html, '<script>alert')) {
    $failures[] = '제목의 script 태그가 escape되어야 한다.';
}

if (!str_contains($html, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')) {
    $failures[] = '제목이 올바르게 escape되어야 한다.';
}

// (13) XSS 공격으로부터 보호 - 설명 escape
$html = $emptyState->render(
    '문서가 없습니다',
    '<img src=x onerror="alert(\'xss\')">'
);

if (str_contains($html, '<img src=x onerror=')) {
    $failures[] = '설명의 img 태그가 escape되어야 한다.';
}

// (14) XSS 공격으로부터 보호 - 액션 URL escape
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['href' => 'javascript:alert("xss")', 'label' => '클릭']
);

if (!str_contains($html, 'href="javascript:alert(&quot;xss&quot;)')) {
    $failures[] = '액션 href가 올바르게 escape되어야 한다.';
}

// (15) XSS 공격으로부터 보호 - 액션 label escape
$html = $emptyState->render(
    '문서가 없습니다',
    null,
    ['href' => '/create', 'label' => '<script>alert("xss")</script>']
);

if (str_contains($html, '<script>alert')) {
    $failures[] = '액션 label의 script 태그가 escape되어야 한다.';
}

// (16) 특수 문자 escape - 제목
$html = $emptyState->render('제목 & < > " \'');

if (!str_contains($html, '제목 &amp; &lt; &gt; &quot; &#039;')) {
    $failures[] = '제목의 특수 문자들이 올바르게 escape되어야 한다.';
}

// (17) 특수 문자 escape - 설명
$html = $emptyState->render('제목', '설명 & < > " \'');

if (!str_contains($html, '설명 &amp; &lt; &gt; &quot; &#039;')) {
    $failures[] = '설명의 특수 문자들이 올바르게 escape되어야 한다.';
}

// (18) 특수 문자 escape - 액션 label
$html = $emptyState->render(
    '제목',
    null,
    ['href' => '/test', 'label' => '버튼 & < >']
);

if (!str_contains($html, '버튼 &amp; &lt; &gt;')) {
    $failures[] = '액션 label의 특수 문자들이 올바르게 escape되어야 한다.';
}

// (19) 기본 Escaper 사용
$emptyStateDefault = new EmptyState();
$html = $emptyStateDefault->render(
    '<script>alert("test")</script>',
    null,
    null
);

if (str_contains($html, '<script>alert')) {
    $failures[] = '기본 Escaper를 사용할 때도 script 태그가 escape되어야 한다.';
}

// (20) 여러 줄 URL 처리
$html = $emptyState->render(
    '검색 결과',
    '결과가 없습니다.',
    ['href' => '/search?query=test&sort=name&page=1', 'label' => '검색']
);

if (!str_contains($html, 'href="/search?query=test&amp;sort=name&amp;page=1')) {
    $failures[] = '복수 쿼리 매개변수가 있는 URL이 올바르게 escape되어야 한다.';
}

// (21) 한국어 텍스트 처리
$html = $emptyState->render(
    '검색 결과가 없습니다',
    '다른 키워드로 검색해보세요',
    ['href' => '/search', 'label' => '다시 검색하기']
);

if (!str_contains($html, '검색 결과가 없습니다')) {
    $failures[] = '한국어 제목이 올바르게 렌더링되어야 한다.';
}

if (!str_contains($html, '다른 키워드로 검색해보세요')) {
    $failures[] = '한국어 설명이 올바르게 렌더링되어야 한다.';
}

if (!str_contains($html, '다시 검색하기')) {
    $failures[] = '한국어 액션 label이 올바르게 렌더링되어야 한다.';
}

// (22) 구조 확인 - 순서
$html = $emptyState->render(
    '제목',
    '설명',
    ['href' => '/test', 'label' => '액션']
);

$titlePos = strpos($html, 'empty-state__title');
$descriptionPos = strpos($html, 'empty-state__description');
$actionPos = strpos($html, 'empty-state__action');

if (!($titlePos < $descriptionPos && $descriptionPos < $actionPos)) {
    $failures[] = 'title, description, action 순서가 유지되어야 한다.';
}

// (23) 경로 URL 처리
$html = $emptyState->render(
    '문서',
    null,
    ['href' => '/docs/create?template=blank', 'label' => '생성']
);

if (!str_contains($html, 'href="/docs/create?template=blank')) {
    $failures[] = '경로와 쿼리 매개변수가 있는 URL이 올바르게 처리되어야 한다.';
}

// (24) 닫는 태그 확인
$html = $emptyState->render('제목');

if (!str_contains($html, '</div>')) {
    $failures[] = '마지막 div 닫는 태그가 있어야 한다.';
}

// div 개수 확인
$openDivCount = substr_count($html, '<div');
$closeDivCount = substr_count($html, '</div>');

if ($openDivCount !== $closeDivCount) {
    $failures[] = '열린 div 태그와 닫힌 div 태그 개수가 일치해야 한다.';
}

// (25) 복잡한 액션 URL
$html = $emptyState->render(
    '최근 활동이 없습니다',
    '활동을 시작해보세요',
    ['href' => 'http://example.com/path?a=1&b=2#section', 'label' => '시작하기']
);

if (!str_contains($html, 'href="http://example.com/path?a=1&amp;b=2#section')) {
    $failures[] = '복잡한 URL의 &가 &amp;로 escape되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "EmptyState 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "EmptyState 테스트 통과.\n");
exit(0);
