<?php

declare(strict_types=1);

/**
 * UI 필드 XSS 회귀 테스트 (tests/fixtures/xss/ui_field_xss_regression.json).
 *
 * 문서 제목, 리비전 소스, 요약(코멘트), 신고 등의 필드에 XSS payload들이
 * 포함된 경우, Escaper를 통해 완전히 이스케이프되어 위험한 raw 마크업이
 * 남지 않는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;

$fixturePath = __DIR__ . '/../fixtures/xss/ui_field_xss_regression.json';

if (!is_file($fixturePath)) {
    fwrite(STDERR, "UI 필드 XSS 회귀 fixture 파일을 찾을 수 없습니다: {$fixturePath}\n");
    exit(1);
}

$fixture = json_decode((string) file_get_contents($fixturePath), true);

if (!is_array($fixture) || !isset($fixture['cases']) || !is_array($fixture['cases'])) {
    fwrite(STDERR, "UI 필드 XSS 회귀 fixture 형식이 올바르지 않습니다: {$fixturePath}\n");
    exit(1);
}

$failures = [];
$escaper = new Escaper();

foreach ($fixture['cases'] as $index => $case) {
    $name = is_array($case) && isset($case['name']) ? (string) $case['name'] : "case #{$index}";
    $field = is_array($case) && isset($case['field']) ? (string) $case['field'] : 'unknown';

    if (!is_array($case) || !array_key_exists('payload', $case)) {
        $failures[] = "{$name}: fixture case에 payload가 있어야 한다.";
        continue;
    }

    $payload = (string) $case['payload'];
    $safeInHtml = is_array($case) && isset($case['safe_in_html']) ? (bool) $case['safe_in_html'] : false;

    // Payload를 Escaper를 통해 이스케이프한다.
    $escaped = $escaper->html($payload);

    // safe_in_html이 true인 경우, 이스케이프된 결과에 위험한 raw 마크업 문자가 없어야 한다.
    if ($safeInHtml) {
        foreach (['<', '>', '"'] as $dangerous) {
            if (str_contains($escaped, $dangerous)) {
                $failures[] = "{$name} ({$field}): 이스케이프 결과에 위험한 raw 문자 '{$dangerous}'가 남아 있다. payload={$payload}, escaped={$escaped}";
            }
        }
    }

    // attribute() 메서드도 동일하게 이스케이프해야 한다.
    $escapedAttr = $escaper->attribute($payload);
    if ($escapedAttr !== $escaped) {
        $failures[] = "{$name} ({$field}): attribute()가 html()과 다르게 이스케이프했다. html={$escaped}, attribute={$escapedAttr}";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "UI 필드 XSS 회귀 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI 필드 XSS 회귀 테스트 통과.\n");
exit(0);
