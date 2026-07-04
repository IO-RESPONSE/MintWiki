<?php

declare(strict_types=1);

/**
 * MintWiki\App 로그 writer 뼈대와 파일 fallback 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;
use MintWiki\App\FileLogWriter;
use MintWiki\App\LogWriter;
use MintWiki\App\StoragePathConfig;

$failures = [];
$testDir = sys_get_temp_dir() . '/mintwiki-log-writer-test-' . bin2hex(random_bytes(4));

try {
    if (!interface_exists(LogWriter::class)) {
        $failures[] = 'LogWriter 인터페이스가 오토로드되어야 한다.';
    }

    $logFile = $testDir . '/logs/app.log';
    $writer = new FileLogWriter($logFile);

    if (!$writer instanceof LogWriter) {
        $failures[] = 'FileLogWriter는 LogWriter를 구현해야 한다.';
    }

    $writer->write('info', '설치 로그 테스트', ['request_id' => 'req_test_123']);

    if (!is_file($logFile)) {
        $failures[] = 'FileLogWriter는 로그 디렉터리를 만들고 파일에 기록해야 한다.';
    } else {
        $lines = file($logFile, FILE_IGNORE_NEW_LINES);
        if ($lines === false || count($lines) !== 1) {
            $failures[] = 'FileLogWriter는 로그 한 줄을 append해야 한다.';
        } else {
            $record = json_decode($lines[0], true);
            if (!is_array($record)) {
                $failures[] = 'FileLogWriter는 JSON line 형식으로 기록해야 한다.';
            } else {
                if (($record['level'] ?? '') !== 'INFO') {
                    $failures[] = 'FileLogWriter는 level을 대문자로 정규화해야 한다.';
                }

                if (($record['message'] ?? '') !== '설치 로그 테스트') {
                    $failures[] = 'FileLogWriter는 message를 보존해야 한다.';
                }

                if (($record['context']['request_id'] ?? '') !== 'req_test_123') {
                    $failures[] = 'FileLogWriter는 context를 함께 기록해야 한다.';
                }

                if (!isset($record['timestamp']) || !is_string($record['timestamp'])) {
                    $failures[] = 'FileLogWriter는 timestamp를 기록해야 한다.';
                }
            }
        }
    }

    $storage = new StoragePathConfig(new ConfigLoader([]), $testDir . '/storage');
    $fromStorage = FileLogWriter::fromStoragePath($storage, 'fallback.log');
    $fromStorage->write('warning', 'storage path 기반 로그');

    if (!is_file($testDir . '/storage/logs/fallback.log')) {
        $failures[] = 'FileLogWriter::fromStoragePath는 StoragePathConfig의 logsPath를 사용해야 한다.';
    }

    file_put_contents($testDir . '/blocked-parent', 'not a directory');
    $fallbackWriter = new FileLogWriter($testDir . '/blocked-parent/app.log');
    $fallbackWriter->write('error', '파일 로그 fallback 테스트');
} finally {
    removeTestPath($testDir);
}

if ($failures !== []) {
    fwrite(STDERR, "LogWriter 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LogWriter 테스트 통과.\n");
exit(0);

/**
 * @param string $path 테스트 임시 경로
 */
function removeTestPath(string $path): void
{
    if (!file_exists($path)) {
        return;
    }

    if (is_file($path) || is_link($path)) {
        @unlink($path);
        return;
    }

    $items = scandir($path);
    if ($items === false) {
        return;
    }

    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }

        removeTestPath($path . DIRECTORY_SEPARATOR . $item);
    }

    @rmdir($path);
}
