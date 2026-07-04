<?php

declare(strict_types=1);

namespace MintWiki\App;

use JsonException;

/**
 * 공유 호스팅 기본 파일 로그 writer.
 *
 * 파일 시스템 쓰기가 불가능한 환경에서는 예외를 전파하지 않고 PHP 기본
 * error_log로 fallback한다.
 */
final class FileLogWriter implements LogWriter
{
    public function __construct(
        private readonly string $logFile
    ) {
    }

    public static function fromStoragePath(StoragePathConfig $storagePathConfig, string $filename = 'app.log'): self
    {
        return new self($storagePathConfig->logsPath() . '/' . $filename);
    }

    /**
     * @param array<string, mixed> $context 로그에 함께 남길 부가 정보
     */
    public function write(string $level, string $message, array $context = []): void
    {
        $line = $this->formatLine($level, $message, $context);
        $directory = dirname($this->logFile);

        if (!is_dir($directory) && !@mkdir($directory, 0775, true) && !is_dir($directory)) {
            error_log($line);
            return;
        }

        if (@file_put_contents($this->logFile, $line . PHP_EOL, FILE_APPEND | LOCK_EX) === false) {
            error_log($line);
        }
    }

    /**
     * @param array<string, mixed> $context 로그에 함께 남길 부가 정보
     */
    private function formatLine(string $level, string $message, array $context): string
    {
        $record = [
            'timestamp' => gmdate(DATE_ATOM),
            'level' => strtoupper(trim($level)),
            'message' => $message,
            'context' => $context,
        ];

        try {
            return json_encode($record, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        } catch (JsonException) {
            $record['context'] = ['encoding_error' => 'context_json_encode_failed'];

            $fallbackLine = json_encode($record, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            if ($fallbackLine === false) {
                return '{"level":"ERROR","message":"log_record_json_encode_failed","context":{}}';
            }

            return $fallbackLine;
        }
    }
}
