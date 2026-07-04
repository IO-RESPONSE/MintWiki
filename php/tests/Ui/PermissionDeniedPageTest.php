<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\PermissionDeniedPage`의 동작을 확인하는 smoke test (태스크 0539).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 권한 거부 page가 올바르게 렌더링되는지
 * 확인한다. ACL 거부 상태를 표시하고 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Acl\Decision;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new PermissionDeniedPage($escaper, $layout);

// ACL 거부 결정 객체 생성
$decision = new Decision(
    permission: 'document.edit',
    allowed: false,
    reason: 'acl.no_matching_rule',
    matchedRuleId: null
);

// (1) 기본 권한 거부 page 렌더링
$html = $page->render($decision);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '권한 거부 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>권한 없음</title>')) {
    $failures[] = '권한 거부 page의 title이 "권한 없음"이어야 한다.';
}

if (!str_contains($html, '<h1>권한 없음</h1>')) {
    $failures[] = '권한 거부 page가 h1으로 "권한 없음"을 표시해야 한다.';
}

if (!str_contains($html, '<p>이 작업을 수행할 권한이 없습니다.</p>')) {
    $failures[] = '권한 거부 page가 거부 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<dt>권한:</dt>')) {
    $failures[] = '권한 거부 page가 "권한:" 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<dd>document.edit</dd>')) {
    $failures[] = '권한 거부 page가 거부된 권한을 표시해야 한다.';
}

if (!str_contains($html, '<dt>이유:</dt>')) {
    $failures[] = '권한 거부 page가 "이유:" 레이블을 포함해야 한다.';
}

if (!str_contains($html, '<dd>acl.no_matching_rule</dd>')) {
    $failures[] = '권한 거부 page가 거부 이유를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '권한 거부 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '권한 거부 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '권한 거부 page가 footer landmark를 포함해야 한다.';
}

// (2) XSS 방지 확인: 특수 문자 escaping
$xssDecision = new Decision(
    permission: 'document.edit<script>',
    allowed: false,
    reason: 'acl.no_matching_rule&alert("xss")',
    matchedRuleId: null
);

$xssHtml = $page->render($xssDecision);

if (str_contains($xssHtml, '<script>')) {
    $failures[] = '권한 거부 page가 권한 필드에서 script 태그를 escape해야 한다.';
}

if (str_contains($xssHtml, '&alert("xss")')) {
    $failures[] = '권한 거부 page가 이유 필드에서 앰퍼샌드를 escape해야 한다.';
}

if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '권한 거부 page가 <를 &lt;로 escape해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "PermissionDeniedPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PermissionDeniedPage 테스트 통과.\n");
exit(0);
