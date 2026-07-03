<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AdminDangerConfirmation`의 동작을 확인하는 smoke test (태스크 0574).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 위험 작업 확인 컴포넌트가 올바르게
 * 렌더링되고, 모든 사용자 입력은 escape되어야 한다. 확인 체크박스와
 * 접근성 속성들이 포함되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AdminDangerConfirmation;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 component 생성
$escaper = new Escaper();
$confirmation = new AdminDangerConfirmation($escaper);

// (1) 기본 위험 확인 렌더링
$html = $confirmation->render(
    '사용자 차단',
    '이 작업은 돌이킬 수 없습니다. 사용자가 완전히 차단됩니다.',
    '네, 이 작업을 수행하겠습니다',
    'confirm_block_user'
);

if (!str_contains($html, '<div class="admin-danger-confirmation"')) {
    $failures[] = '위험 확인이 admin-danger-confirmation 클래스를 포함해야 한다.';
}

if (!str_contains($html, 'role="alert"')) {
    $failures[] = '위험 확인이 role="alert"를 포함해야 한다.';
}

if (!str_contains($html, '<strong class="admin-danger-confirmation__title">⚠️ 사용자 차단</strong>')) {
    $failures[] = '위험 확인이 경고 아이콘과 제목을 포함해야 한다.';
}

if (!str_contains($html, '<p class="admin-danger-confirmation__message">이 작업은 돌이킬 수 없습니다. 사용자가 완전히 차단됩니다.</p>')) {
    $failures[] = '위험 확인이 메시지를 포함해야 한다.';
}

if (!str_contains($html, '<input type="checkbox" name="confirm_block_user" value="1" required aria-required="true">')) {
    $failures[] = '위험 확인이 필수 체크박스를 포함해야 한다.';
}

if (!str_contains($html, 'aria-required="true"')) {
    $failures[] = '위험 확인이 aria-required="true"를 포함해야 한다.';
}

if (!str_contains($html, 'required')) {
    $failures[] = '위험 확인 체크박스가 required 속성을 포함해야 한다.';
}

if (!str_contains($html, '네, 이 작업을 수행하겠습니다')) {
    $failures[] = '위험 확인이 확인 레이블을 포함해야 한다.';
}

// (2) 제목의 XSS escape 확인
$xssTitleHtml = $confirmation->render(
    '<script>alert("xss")</script>',
    '메시지',
    '확인',
    'confirm'
);

if (str_contains($xssTitleHtml, '<script>')) {
    $failures[] = '제목의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssTitleHtml, '&lt;script&gt;')) {
    $failures[] = '제목이 &lt;script&gt;로 escape되어야 한다.';
}

// (3) 메시지의 XSS escape 확인
$xssMessageHtml = $confirmation->render(
    '제목',
    '<img src=x onerror=alert(1)>',
    '확인',
    'confirm'
);

if (str_contains($xssMessageHtml, '<img src=x onerror')) {
    $failures[] = '메시지의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssMessageHtml, '&lt;img src=x onerror')) {
    $failures[] = '메시지가 escape되어야 한다.';
}

// (4) 확인 레이블의 XSS escape 확인
$xssLabelHtml = $confirmation->render(
    '제목',
    '메시지',
    '" onclick="alert(1)"',
    'confirm'
);

if (str_contains($xssLabelHtml, '" onclick=')) {
    $failures[] = '확인 레이블의 onclick 속성 breakout은 escape되어야 한다.';
}

if (!str_contains($xssLabelHtml, '&quot; onclick=')) {
    $failures[] = '확인 레이블이 escape되어야 한다.';
}

// (5) 입력 이름의 XSS escape 확인
$xssInputNameHtml = $confirmation->render(
    '제목',
    '메시지',
    '확인',
    '<svg onload=alert(1)>'
);

if (str_contains($xssInputNameHtml, '<svg onload')) {
    $failures[] = '입력 이름의 svg 태그는 escape되어야 한다.';
}

if (!str_contains($xssInputNameHtml, 'name="&lt;svg onload')) {
    $failures[] = '입력 이름이 escape되어야 한다.';
}

// (6) 특수 문자 escape 확인
$specialHtml = $confirmation->render(
    '제목 & 위험',
    '메시지 < > "테스트"',
    '확인 & 진행',
    'confirm_test'
);

if (!str_contains($specialHtml, '제목 &amp; 위험')) {
    $failures[] = '제목의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '메시지 &lt; &gt; &quot;테스트&quot;')) {
    $failures[] = '메시지의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '확인 &amp; 진행')) {
    $failures[] = '확인 레이블의 특수 문자들이 escape되어야 한다.';
}

// (7) 빈 필드 처리 - 빈 제목
$emptyTitleHtml = $confirmation->render('', '메시지', '확인', 'confirm');
if (!empty($emptyTitleHtml)) {
    $failures[] = '빈 제목은 빈 문자열을 반환해야 한다.';
}

// (8) 빈 필드 처리 - 빈 메시지
$emptyMessageHtml = $confirmation->render('제목', '', '확인', 'confirm');
if (!empty($emptyMessageHtml)) {
    $failures[] = '빈 메시지는 빈 문자열을 반환해야 한다.';
}

// (9) 빈 필드 처리 - 빈 확인 레이블
$emptyLabelHtml = $confirmation->render('제목', '메시지', '', 'confirm');
if (!empty($emptyLabelHtml)) {
    $failures[] = '빈 확인 레이블은 빈 문자열을 반환해야 한다.';
}

// (10) 빈 필드 처리 - 빈 입력 이름
$emptyInputNameHtml = $confirmation->render('제목', '메시지', '확인', '');
if (!empty($emptyInputNameHtml)) {
    $failures[] = '빈 입력 이름은 빈 문자열을 반환해야 한다.';
}

// (11) 다양한 입력 이름 확인
$customInputNameHtml = $confirmation->render(
    '문서 삭제',
    '이 문서는 영구적으로 삭제됩니다.',
    '네, 삭제하겠습니다',
    'confirm_delete_document'
);

if (!str_contains($customInputNameHtml, 'name="confirm_delete_document"')) {
    $failures[] = 'input 이름이 올바르게 렌더링되어야 한다.';
}

// (12) 메시지에 개행 포함
$multilineMessageHtml = $confirmation->render(
    '제목',
    "줄 1\n줄 2\n줄 3",
    '확인',
    'confirm'
);

if (!str_contains($multilineMessageHtml, '줄 1')) {
    $failures[] = '메시지의 첫 번째 줄이 포함되어야 한다.';
}

if (!str_contains($multilineMessageHtml, '줄 2')) {
    $failures[] = '메시지의 두 번째 줄이 포함되어야 한다.';
}

if (!str_contains($multilineMessageHtml, '줄 3')) {
    $failures[] = '메시지의 세 번째 줄이 포함되어야 한다.';
}

// (13) 모든 필드가 HTML에 포함되는지 확인
$completenessHtml = $confirmation->render(
    '사용자 차단',
    '이 작업은 돌이킬 수 없습니다.',
    '네, 이해했습니다',
    'confirm_action'
);

if (!str_contains($completenessHtml, 'class="admin-danger-confirmation__header"')) {
    $failures[] = '위험 확인이 header 섹션을 포함해야 한다.';
}

if (!str_contains($completenessHtml, 'class="admin-danger-confirmation__message"')) {
    $failures[] = '위험 확인이 message 섹션을 포함해야 한다.';
}

if (!str_contains($completenessHtml, 'class="admin-danger-confirmation__confirm-label"')) {
    $failures[] = '위험 확인이 confirm-label 섹션을 포함해야 한다.';
}

// (14) 체크박스 value 속성 확인
$checkboxValueHtml = $confirmation->render('제목', '메시지', '확인', 'confirm');
if (!str_contains($checkboxValueHtml, 'value="1"')) {
    $failures[] = '체크박스의 value가 "1"이어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AdminDangerConfirmation 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminDangerConfirmation 테스트 통과.\n");
exit(0);
