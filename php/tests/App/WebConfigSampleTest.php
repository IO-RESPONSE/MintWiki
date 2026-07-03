<?php

declare(strict_types=1);

/**
 * 웹호스팅 설정 샘플 검증.
 *
 * php/config/ 디렉토리에 웹 서버 및 데이터베이스 설정 샘플이
 * 올바르게 배치되어 있는지 확인한다.
 *
 * @see docs/shared-hosting-target-baseline.md
 * @see docs/public-docroot-policy.md
 *
 * 외부 테스트 프레임워크 없이 php CLI로 직접 실행된다.
 * 성공(exit 0), 실패(exit 1)로 결과를 알린다.
 */

$phpRoot = dirname(__DIR__, 2);
$configDir = $phpRoot . '/config';

$failures = [];

// 1. config/ 디렉토리 존재
if (!is_dir($configDir)) {
    $failures[] = 'config/ directory must exist';
}

// 2. database.php.sample 파일 존재
$databaseSampleFile = $configDir . '/database.php.sample';
if (!file_exists($databaseSampleFile)) {
    $failures[] = 'database.php.sample must exist for database configuration example';
}

// 3. database.php.sample은 PHP 파일
if (file_exists($databaseSampleFile)) {
    $content = file_get_contents($databaseSampleFile);
    if (!str_starts_with($content, '<?php')) {
        $failures[] = 'database.php.sample must be a PHP file (start with <?php)';
    }
    // return 문으로 끝나야 함 (설정 배열 반환)
    if (!str_contains($content, 'return [')) {
        $failures[] = 'database.php.sample must return a configuration array';
    }
}

// 4. .env.sample 파일 존재
$envSampleFile = $configDir . '/.env.sample';
if (!file_exists($envSampleFile)) {
    $failures[] = '.env.sample must exist for environment variable example';
}

// 5. .env.sample은 텍스트 파일이고 주석으로 시작
if (file_exists($envSampleFile)) {
    $content = file_get_contents($envSampleFile);
    if (!str_starts_with($content, '#')) {
        $failures[] = '.env.sample should start with a comment (#)';
    }
    // 주요 환경 변수 예시 포함
    if (!str_contains($content, 'WIKI_')) {
        $failures[] = '.env.sample must contain example WIKI_* environment variables';
    }
    if (!str_contains($content, 'WIKI_MARIADB_DSN')) {
        $failures[] = '.env.sample must include WIKI_MARIADB_DSN for MariaDB connection';
    }
}

// 6. web.config.sample 파일 존재
$webConfigSampleFile = $configDir . '/web.config.sample';
if (!file_exists($webConfigSampleFile)) {
    $failures[] = 'web.config.sample must exist for IIS web server configuration';
}

// 7. web.config.sample은 XML 파일
if (file_exists($webConfigSampleFile)) {
    $content = file_get_contents($webConfigSampleFile);
    if (!str_contains($content, '<?xml') || !str_contains($content, '<configuration>')) {
        $failures[] = 'web.config.sample must be a valid XML file with <configuration> root';
    }
    // URL rewrite 설정 포함
    if (!str_contains($content, '<rewrite>')) {
        $failures[] = 'web.config.sample must include rewrite configuration for front controller';
    }
    // Front controller 라우팅 포함
    if (!str_contains($content, 'index.php')) {
        $failures[] = 'web.config.sample must reference index.php (front controller)';
    }
}

// 8. config/ 디렉토리는 public/ 외부에 있어야 함
$publicDir = $phpRoot . '/public';
if (is_dir($configDir) && is_dir($publicDir)) {
    if (str_starts_with($configDir, $publicDir)) {
        $failures[] = 'config/ must not be inside public/ (security: database credentials)';
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Web Config Sample validation 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Web Config Sample validation 통과: 웹호스팅 설정 샘플 확인 완료.\n");
exit(0);
