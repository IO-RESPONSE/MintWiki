<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\FormErrorSummary`의 동작을 확인하는 smoke test (태스크 0542).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 폼 오류 요약이 올바르게 렌더링되는지
 * 확인한다. 모든 오류 메시지는 escape되어야 하고, 접근성 속성을 포함해야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\FormErrorSummary;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper 생성
$escaper = new Escaper();
$errorSummary = new FormErrorSummary($escaper);

// (1) 오류가 없을 때 빈 문자열 반환
$html = $errorSummary->render([]);
if ($html !== '') {
    $failures[] = '오류가 없을 때 빈 문자열을 반환해야 한다.';
}

// (2) 단일 필드에 단일 오류
$html = $errorSummary->render(['title' => '제목은 필수입니다']);

if (!str_contains($html, '<div role="alert"')) {
    $failures[] = '오류 요약이 role="alert"를 포함해야 한다.';
}

if (!str_contains($html, 'aria-label="오류 요약"')) {
    $failures[] = '오류 요약이 aria-label="오류 요약"를 포함해야 한다.';
}

if (!str_contains($html, '<strong>오류가 발생했습니다</strong>')) {
    $failures[] = '오류 요약이 "오류가 발생했습니다" 메시지를 포함해야 한다.';
}

if (!str_contains($html, '<ul>')) {
    $failures[] = '오류 요약이 ul 요소를 포함해야 한다.';
}

if (!str_contains($html, '<li>제목은 필수입니다</li>')) {
    $failures[] = '오류 요약이 오류 메시지를 li 요소로 감싸야 한다.';
}

if (!str_contains($html, '</ul>')) {
    $failures[] = '오류 요약이 ul 닫음 태그를 포함해야 한다.';
}

// (3) 단일 필드에 복수 오류
$html = $errorSummary->render(['email' => [
    '이메일 주소는 필수입니다',
    '유효한 이메일 형식이 아닙니다',
]]);

if (!str_contains($html, '<li>이메일 주소는 필수입니다</li>')) {
    $failures[] = '오류 요약이 첫 번째 오류를 포함해야 한다.';
}

if (!str_contains($html, '<li>유효한 이메일 형식이 아닙니다</li>')) {
    $failures[] = '오류 요약이 두 번째 오류를 포함해야 한다.';
}

// (4) 복수 필드에 복수 오류
$html = $errorSummary->render([
    'title' => '제목은 필수입니다',
    'content' => [
        '내용은 필수입니다',
        '내용은 최소 10자 이상이어야 합니다',
    ],
]);

if (!str_contains($html, '<li>제목은 필수입니다</li>')) {
    $failures[] = '복수 필드에서 첫 필드 오류를 포함해야 한다.';
}

if (!str_contains($html, '<li>내용은 필수입니다</li>')) {
    $failures[] = '복수 필드에서 두 번째 필드 첫 오류를 포함해야 한다.';
}

if (!str_contains($html, '<li>내용은 최소 10자 이상이어야 합니다</li>')) {
    $failures[] = '복수 필드에서 두 번째 필드 두 번째 오류를 포함해야 한다.';
}

// (5) XSS 공격으로부터 보호 - 단일 오류 문자열 escape
$html = $errorSummary->render([
    'field' => '<script>alert("xss")</script>',
]);

if (str_contains($html, '<script>alert')) {
    $failures[] = '단일 오류 문자열의 script 태그가 escape되어야 한다.';
}

if (!str_contains($html, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')) {
    $failures[] = '단일 오류 문자열이 올바르게 escape되어야 한다.';
}

// (6) XSS 공격으로부터 보호 - 배열 오류 escape
$html = $errorSummary->render([
    'field' => [
        '<img src=x onerror="alert(\'xss\')">',
    ],
]);

if (str_contains($html, '<img src=x onerror=')) {
    $failures[] = '배열 오류의 img 태그가 escape되어야 한다.';
}

if (!str_contains($html, '&lt;img src=x onerror=')) {
    $failures[] = '배열 오류가 올바르게 escape되어야 한다.';
}

// (7) 특수 문자 escape
$html = $errorSummary->render([
    'field' => '필드 & < > " \'',
]);

if (!str_contains($html, '필드 &amp; &lt; &gt; &quot; &#039;')) {
    $failures[] = '특수 문자들이 올바르게 escape되어야 한다.';
}

// (8) Escaper 주입 없이 기본 Escaper 사용
$errorSummaryDefault = new FormErrorSummary();
$html = $errorSummaryDefault->render(['field' => '<script>alert("test")</script>']);

if (str_contains($html, '<script>alert')) {
    $failures[] = '기본 Escaper를 사용할 때도 script 태그가 escape되어야 한다.';
}

// (9) 닫음 div 태그 확인
$html = $errorSummary->render(['field' => '오류']);

if (!str_contains($html, '</div>')) {
    $failures[] = '오류 요약이 div 닫음 태그를 포함해야 한다.';
}

// (10) 접근성: role과 aria-label의 순서 확인
if (!preg_match('/<div role="alert" aria-label="오류 요약">/', $html)) {
    $failures[] = 'div 요소가 올바른 순서로 role과 aria-label을 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "FormErrorSummary 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FormErrorSummary 테스트 통과.\n");
exit(0);
