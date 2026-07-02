<?php

declare(strict_types=1);

/**
 * MintWiki\Document\Title::normalize()의 정규화 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0400 DocumentTest.php와 동일한 방식).
 *
 * 케이스 값은 Python `normalize_title`(src/modules/document/title.py)의
 * cross-language fixture(tests/modules/document/fixtures/)와 맞춘다. fixture
 * 파일을 직접 읽어 들이는 범용 러너는 0426(PHP document fixture parity
 * tests)에서 추가된다 — 여기서는 같은 시나리오를 손으로 옮겨 결과만
 * 맞춘다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\Title;

$failures = [];

$successCases = [
    // [설명, 입력, 기대값] — tests/modules/document/fixtures/*.json 과 동일한 값.
    ['앞뒤 공백을 제거한다.', '  hello  ', 'hello'],
    ['앞뒤 탭/개행을 제거한다.', "\n\thello\t\n", 'hello'],
    ['내부 연속 공백을 단일 공백으로 축소한다.', 'hello   world', 'hello world'],
    ['양 끝 제거와 내부 축소를 동시에 수행한다.', '  a   b   c  ', 'a b c'],
    ['한글 제목의 공백만 제거하고 내용은 유지한다.', '  한글 제목  ', '한글 제목'],
    ['혼합 언어/특수문자/숫자 제목을 정규화한다.', '  Document 한글 Title: Chapter 3  ', 'Document 한글 Title: Chapter 3'],
];

foreach ($successCases as [$description, $input, $expected]) {
    $actual = Title::normalize($input);
    if ($actual !== $expected) {
        $failures[] = "{$description} (입력: " . var_export($input, true) . ") 기대값 " . var_export($expected, true) . ", 실제값 " . var_export($actual, true);
    }
}

$rejectionCases = [
    ['빈 문자열을 거부한다.', ''],
    ['공백만 있는 제목을 거부한다.', '   '],
    ['탭과 개행만 섞인 제목을 거부한다.', "\t\n\t"],
];

foreach ($rejectionCases as [$description, $input]) {
    try {
        Title::normalize($input);
        $failures[] = "{$description} EmptyTitleError를 던지지 않았다.";
    } catch (EmptyTitleError $error) {
        // 정상 경로 — 아무 것도 하지 않는다.
    }
}

if (EmptyTitleError::CODE !== 'document.empty_title') {
    $failures[] = 'EmptyTitleError::CODE는 document.empty_title이어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Title 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Title 테스트 통과.\n");
exit(0);
