<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\AssetVersioning의 asset URL 버전 쿼리 생성을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AssetVersioning;

$failures = [];
$testDir = sys_get_temp_dir() . '/asset_versioning_test_' . uniqid();
mkdir($testDir);

// 테스트 asset 파일 생성
$cssDir = $testDir . '/assets/css';
mkdir($cssDir, 0755, true);
file_put_contents($cssDir . '/design-tokens.css', 'body { color: red; }');

$jsDir = $testDir . '/assets/js';
mkdir($jsDir, 0755, true);
file_put_contents($jsDir . '/app.js', 'console.log("hello");');

$versioningWithTestDir = new AssetVersioning($testDir);

// 테스트 1: 기본 URL 생성
$url = $versioningWithTestDir->url('/assets/css/design-tokens.css');
if (!str_starts_with($url, '/assets/css/design-tokens.css?v=')) {
    $failures[] = 'URL이 올바른 형식이어야 한다.';
}

if (!preg_match('/\?v=[a-f0-9]{8}$/', $url)) {
    $failures[] = 'URL이 8자 16진수 해시 쿼리를 포함해야 한다.';
}

// 테스트 2: 파일 내용이 같으면 같은 해시를 반환해야 함
$url1 = $versioningWithTestDir->url('/assets/css/design-tokens.css');
$url2 = $versioningWithTestDir->url('/assets/css/design-tokens.css');
if ($url1 !== $url2) {
    $failures[] = '같은 파일 내용은 같은 해시를 생성해야 한다.';
}

// 테스트 3: 다른 파일은 다른 해시를 반환해야 함
$urlCss = $versioningWithTestDir->url('/assets/css/design-tokens.css');
$urlJs = $versioningWithTestDir->url('/assets/js/app.js');
if ($urlCss === $urlJs) {
    $failures[] = '다른 파일은 다른 해시를 생성해야 한다.';
}

// 테스트 4: 파일 내용 변경 후 다른 해시를 반환해야 함
$urlBefore = $versioningWithTestDir->url('/assets/css/design-tokens.css');
file_put_contents($cssDir . '/design-tokens.css', 'body { color: blue; }');
$urlAfter = $versioningWithTestDir->url('/assets/css/design-tokens.css');
if ($urlBefore === $urlAfter) {
    $failures[] = '파일 내용 변경 후 해시가 변경되어야 한다.';
}

// 테스트 5: /assets로 시작하지 않는 경로는 예외 발생
try {
    $versioningWithTestDir->url('/css/design-tokens.css');
    $failures[] = '/assets로 시작하지 않는 경로는 RuntimeException을 발생시켜야 한다.';
} catch (RuntimeException $e) {
    if (!str_contains($e->getMessage(), '/assets/')) {
        $failures[] = 'RuntimeException 메시지가 경로 요구사항을 포함해야 한다.';
    }
}

// 테스트 6: 존재하지 않는 파일은 예외 발생
try {
    $versioningWithTestDir->url('/assets/css/nonexistent.css');
    $failures[] = '존재하지 않는 파일은 RuntimeException을 발생시켜야 한다.';
} catch (RuntimeException $e) {
    if (!str_contains($e->getMessage(), '찾을 수 없습니다')) {
        $failures[] = 'RuntimeException 메시지가 파일 부재를 명시해야 한다.';
    }
}

// 테스트 7: 경로 순회 공격 방지
try {
    $versioningWithTestDir->url('/assets/../../etc/passwd');
    $failures[] = '경로 순회는 RuntimeException을 발생시켜야 한다.';
} catch (RuntimeException $e) {
    if (!str_contains($e->getMessage(), '유효하지 않습니다')) {
        $failures[] = 'RuntimeException 메시지가 경로 검증을 명시해야 한다.';
    }
}

// 정리
array_map('unlink', glob($cssDir . '/*'));
rmdir($cssDir);
array_map('unlink', glob($jsDir . '/*'));
rmdir($jsDir);
rmdir($testDir . '/assets');
rmdir($testDir);

if ($failures !== []) {
    fwrite(STDERR, "AssetVersioning 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AssetVersioning 테스트 통과.\n");
exit(0);
