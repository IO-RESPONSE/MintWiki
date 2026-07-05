<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentEditorPage`의 문법 삽입 툴바/문법 도움말 마크업을
 * 확인하는 smoke test (태스크 0709).
 *
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 검증 대상:
 * (1) 편집 화면에 툴바(`role="toolbar"`)가 존재하고, Acceptance Criteria가
 *     열거한 7개 버튼(굵게/기울임/밑줄/링크/제목/목록/표)이 각각 대응하는
 *     `data-markup-before`/`data-markup-after` 문법 데이터 속성을 갖는지.
 * (2) 각 툴바 버튼이 `type="button"`이라 JS 없이는 폼을 제출하지 않는지
 *     (점진적 향상 — JS 없이도 편집/저장이 계속 정상 동작해야 한다).
 * (3) 각 버튼이 접근성을 위한 `aria-label`을 갖는지.
 * (4) 접이식 문법 도움말 패널이 `<details>/<summary>`로 구현되어 JS 없이도
 *     펼쳐지는지, 그리고 주요 문법 예시(입력→결과)를 포함하는지.
 * (5) 툴바/도움말에 사용자 입력이 섞이지 않으므로 항상 같은 정적 마크업이
 *     나오지만, escape 경로(Escaper)를 거치는지는 별도로 확인한다(특수문자를
 *     포함한 title/source를 넣어도 툴바/도움말 마크업 자체가 깨지지 않는지).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\DocumentEditorPage;

$failures = [];

// 세션 초기화(CsrfTokenService가 세션을 사용한다)
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

$page = new DocumentEditorPage();
$html = $page->render('테스트 문서', '테스트 문서', '기존 내용');

// (1) 툴바 존재 확인
if (!str_contains($html, '<div class="editor-toolbar" role="toolbar" aria-label="문법 삽입 도구모음" aria-controls="source">')) {
    $failures[] = '편집 화면이 role="toolbar"인 문법 삽입 툴바를 포함해야 한다.';
}

// (1)+(2)+(3) 버튼별 문법 데이터 속성 및 접근성 확인
$expectedButtons = [
    '굵게' => ["'''", "'''"],
    '기울임' => ["''", "''"],
    '밑줄' => ['__', '__'],
    '링크' => ['[[', ']]'],
    '제목' => ['== ', ' =='],
    '목록' => ['* ', ''],
    '표' => ['|| ', ' ||'],
];

foreach ($expectedButtons as $label => [$before, $after]) {
    $escapedBefore = htmlspecialchars($before, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $escapedAfter = htmlspecialchars($after, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $expectedButton = '<button type="button" class="editor-toolbar__button" '
        . 'data-markup-before="' . $escapedBefore . '" data-markup-after="' . $escapedAfter . '" '
        . 'aria-label="' . $label . ' 서식 삽입">' . $label . '</button>';

    if (!str_contains($html, $expectedButton)) {
        $failures[] = "'{$label}' 툴바 버튼이 올바른 data-markup-before/after, aria-label을 가진 type=\"button\"으로 렌더링되어야 한다.";
    }
}

// (4) 접이식 문법 도움말 패널 확인
if (!str_contains($html, '<details class="editor-help">')) {
    $failures[] = '편집 화면이 <details>로 구현된 문법 도움말 패널을 포함해야 한다.';
}

if (!str_contains($html, '<summary>문법 도움말</summary>')) {
    $failures[] = '문법 도움말 패널이 "문법 도움말" summary를 포함해야 한다.';
}

$expectedHelpExamples = [
    ["'''굵게'''", '<strong>굵게</strong>'],
    ["''기울임''", '<em>기울임</em>'],
    ['__밑줄__', '<u>밑줄</u>'],
    ['[[문서제목]]', '<a href="/wiki/문서제목">문서제목</a>'],
    ['== 제목 ==', '<h2>제목</h2>'],
    ['* 목록 항목', '<ul><li>목록 항목</li></ul>'],
    ['||셀1||셀2||', '<table><tbody><tr><td>셀1</td><td>셀2</td></tr></tbody></table>'],
];

foreach ($expectedHelpExamples as [$input, $outputHtml]) {
    $escapedInput = htmlspecialchars($input, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    if (!str_contains($html, '<code class="editor-help__input">' . $escapedInput . '</code>')) {
        $failures[] = "문법 도움말이 입력 예시 '{$input}'를 포함해야 한다.";
    }
    if (!str_contains($html, '<div class="editor-help__output">' . $outputHtml . '</div>')) {
        $failures[] = "문법 도움말이 '{$input}'에 대응하는 결과 '{$outputHtml}'를 포함해야 한다.";
    }
}

// (5) 툴바/도움말 스크립트가 assets/js로 점진적 향상되며, textarea/저장 흐름은 그대로 유지되는지
if (!str_contains($html, '<script src="/assets/js/edit-toolbar.js" defer></script>')) {
    $failures[] = '편집 화면이 점진적 향상 스크립트(edit-toolbar.js)를 defer로 로드해야 한다.';
}

if (!str_contains($html, '<textarea id="source" name="source" required>기존 내용</textarea>')) {
    $failures[] = '툴바/도움말 추가 후에도 textarea가 기존 source 값을 그대로 유지해야 한다.';
}

if (!str_contains($html, '<button type="submit">저장</button>')) {
    $failures[] = '툴바/도움말 추가 후에도 저장 버튼이 그대로 남아 있어야 한다.';
}

// (6) title/source에 특수 문자가 섞여도 툴바/도움말 마크업 자체는 그대로 유지되는지(escape 경로 회귀 방지)
$xssHtml = $page->render('<script>alert(1)</script>', '<script>alert(1)</script>', '<img src=x onerror=1>');

if (!str_contains($xssHtml, '<div class="editor-toolbar" role="toolbar" aria-label="문법 삽입 도구모음" aria-controls="source">')) {
    $failures[] = '특수 문자가 섞인 title/source에도 툴바 마크업이 그대로 렌더링되어야 한다.';
}

if (!str_contains($xssHtml, '<details class="editor-help">')) {
    $failures[] = '특수 문자가 섞인 title/source에도 문법 도움말 패널이 그대로 렌더링되어야 한다.';
}

if (str_contains($xssHtml, '<script>alert(1)</script>')) {
    $failures[] = 'title/source의 script 태그는 escape되어야 한다(툴바/도움말과 무관하게 유지되어야 하는 기존 계약).';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentEditorPage 툴바/도움말 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentEditorPage 툴바/도움말 테스트 통과.\n");
exit(0);
