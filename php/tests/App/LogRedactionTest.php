<?php

declare(strict_types=1);

/**
 * MintWiki\App\FileLogWriter의 민감 정보 마스킹 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\FileLogWriter;

$failures = [];
$testDir = sys_get_temp_dir() . '/mintwiki-log-redaction-test-' . bin2hex(random_bytes(4));
$logFile = $testDir . '/logs/app.log';

try {
    $writer = new FileLogWriter($logFile);
    $writer->write('warning', '민감 정보 마스킹 테스트', [
        'request_id' => 'req_redaction_123',
        'password' => 'plain-db-password',
        'csrf_token' => 'abcdef1234567890',
        'nested' => [
            'apiToken' => 'tok123456789',
            'dbPassword' => 'nested-db-password',
        ],
    ]);

    if (!is_file($logFile)) {
        $failures[] = 'FileLogWriter는 마스킹 테스트 로그 파일을 생성해야 한다.';
    } else {
        $line = file_get_contents($logFile);
        if ($line === false) {
            $failures[] = '마스킹 테스트 로그 파일을 읽을 수 있어야 한다.';
        } else {
            foreach (['plain-db-password', 'abcdef1234567890', 'tok123456789', 'nested-db-password'] as $secret) {
                if (str_contains($line, $secret)) {
                    $failures[] = "로그 원문에 민감값 '{$secret}'이 남으면 안 된다.";
                }
            }

            $record = json_decode($line, true);
            if (!is_array($record)) {
                $failures[] = '마스킹 테스트 로그는 JSON line이어야 한다.';
            } else {
                $context = $record['context'] ?? null;
                if (!is_array($context)) {
                    $failures[] = '마스킹 테스트 로그는 context 객체를 포함해야 한다.';
                } else {
                    if (($context['request_id'] ?? '') !== 'req_redaction_123') {
                        $failures[] = '민감하지 않은 context 값은 보존해야 한다.';
                    }

                    if (($context['password'] ?? '') !== '[REDACTED]') {
                        $failures[] = 'password context 값은 전체 마스킹해야 한다.';
                    }

                    if (($context['csrf_token'] ?? '') !== 'abcdef**********') {
                        $failures[] = 'token context 값은 앞 6자만 남기고 마스킹해야 한다.';
                    }

                    if (($context['nested']['apiToken'] ?? '') !== 'tok123******') {
                        $failures[] = '중첩 token context 값도 마스킹해야 한다.';
                    }

                    if (($context['nested']['dbPassword'] ?? '') !== '[REDACTED]') {
                        $failures[] = '중첩 password context 값도 전체 마스킹해야 한다.';
                    }
                }
            }
        }
    }
} finally {
    removeTestPath($testDir);
}

if ($failures !== []) {
    fwrite(STDERR, "LogRedaction 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LogRedaction 테스트 통과.\n");
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
