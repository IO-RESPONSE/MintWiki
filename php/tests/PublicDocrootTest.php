<?php

declare(strict_types=1);

/**
 * public docroot 정책 검증.
 *
 * public/ 디렉토리가 웹 서버 document root이고, 민감한 파일들이
 * public/ 외부에 있는지 확인한다.
 *
 * @see docs/public-docroot-policy.md
 *
 * 외부 테스트 프레임워크 없이 php CLI로 직접 실행된다.
 * 성공(exit 0), 실패(exit 1)로 결과를 알린다.
 */

$phpRoot = dirname(__DIR__);
$publicDir = $phpRoot . '/public';

$failures = [];

// 1. public/ 디렉토리 존재
if (!is_dir($publicDir)) {
    $failures[] = 'public/ directory must exist at project root';
}

// 2. public/index.php 존재
$indexFile = $publicDir . '/index.php';
if (!file_exists($indexFile)) {
    $failures[] = 'public/index.php (front controller) must exist';
}

// 3. public/index.php는 PHP 파일
if (file_exists($indexFile)) {
    $content = file_get_contents($indexFile);
    if (!str_starts_with($content, '<?php')) {
        $failures[] = 'public/index.php must be a PHP file (start with <?php)';
    }
}

// 4. src/ 디렉토리 존재
$srcDir = $phpRoot . '/src';
if (!is_dir($srcDir)) {
    $failures[] = 'src/ directory must exist';
}

// 5. src/ 는 public/ 외부에 있어야 함
if (str_starts_with($srcDir, $publicDir)) {
    $failures[] = 'src/ must not be inside public/ (security: source code exposure)';
}

// 6. config/ 디렉토리가 있다면 public/ 외부에 있어야 함
$configDir = $phpRoot . '/config';
if (is_dir($configDir) && str_starts_with($configDir, $publicDir)) {
    $failures[] = 'config/ must not be inside public/ (security: database credentials)';
}

// 7. vendor/ 디렉토리가 있다면 public/ 외부에 있어야 함
$vendorDir = $phpRoot . '/vendor';
if (is_dir($vendorDir) && str_starts_with($vendorDir, $publicDir)) {
    $failures[] = 'vendor/ must not be inside public/ (security: dependency source)';
}

// 8. composer.json이 있다면 public/에 없어야 함
$composerJson = $phpRoot . '/composer.json';
if (file_exists($composerJson) && file_exists($publicDir . '/composer.json')) {
    $failures[] = 'composer.json must not be in public/ (security: dependency info)';
}

// 9. composer.lock이 있다면 public/에 없어야 함
$composerLock = $phpRoot . '/composer.lock';
if (file_exists($composerLock) && file_exists($publicDir . '/composer.lock')) {
    $failures[] = 'composer.lock must not be in public/ (security: dependency lock)';
}

// 10. .gitignore이 있다면 public/에 없어야 함
$gitignore = $phpRoot . '/.gitignore';
if (file_exists($gitignore) && file_exists($publicDir . '/.gitignore')) {
    $failures[] = '.gitignore must not be in public/';
}

// 11. tests/ 디렉토리가 있다면 public/ 외부에 있어야 함
$testsDir = $phpRoot . '/tests';
if (is_dir($testsDir) && str_starts_with($testsDir, $publicDir)) {
    $failures[] = 'tests/ must not be in public/ (security: test code exposure)';
}

// 12. docs/ 디렉토리가 있다면 public/ 외부에 있어야 함
$docsDir = $phpRoot . '/docs';
if (is_dir($docsDir) && str_starts_with($docsDir, $publicDir)) {
    $failures[] = 'docs/ must not be in public/';
}

// 13. db/ 디렉토리가 있다면 public/ 외부에 있어야 함
$dbDir = $phpRoot . '/db';
if (is_dir($dbDir) && str_starts_with($dbDir, $publicDir)) {
    $failures[] = 'db/ must not be in public/ (security: schema exposure)';
}

// 14. public/ 디렉토리에 index.php가 있는지 확인
if (is_dir($publicDir)) {
    $items = scandir($publicDir);
    if (!in_array('index.php', $items, true)) {
        $failures[] = 'public/ must contain index.php';
    }
}

// 15. public/.htaccess 파일이 있는지 확인 (태스크 0613)
$htaccessFile = $publicDir . '/.htaccess';
if (!file_exists($htaccessFile)) {
    $failures[] = 'public/.htaccess must exist (front controller rules for Apache)';
}

if ($failures !== []) {
    fwrite(STDERR, "Public Docroot Policy validation 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Public Docroot Policy validation 통과: 디렉토리 구조 확인 완료.\n");
exit(0);
