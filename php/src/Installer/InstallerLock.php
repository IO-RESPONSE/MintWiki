<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use DateTimeImmutable;
use RuntimeException;

/**
 * 설치 완료 후 installer 재실행을 막는 lock file 정책.
 */
final class InstallerLock
{
    public const DEFAULT_FILENAME = 'install.lock';

    private string $lockFile;

    public function __construct(string $lockFile)
    {
        $this->lockFile = $lockFile;
    }

    public function path(): string
    {
        return $this->lockFile;
    }

    public function isLocked(): bool
    {
        return is_file($this->lockFile);
    }

    public function markComplete(?DateTimeImmutable $completedAt = null): void
    {
        $directory = dirname($this->lockFile);

        if (!is_dir($directory)) {
            throw new RuntimeException('installer lock 디렉터리가 없습니다: ' . $directory);
        }

        if (!is_writable($directory)) {
            throw new RuntimeException('installer lock 디렉터리에 쓸 수 없습니다: ' . $directory);
        }

        $completedAt ??= new DateTimeImmutable();
        $content = json_encode([
            'status' => 'complete',
            'completed_at' => $completedAt->format(DATE_ATOM),
        ], JSON_THROW_ON_ERROR);

        if (file_put_contents($this->lockFile, $content . PHP_EOL, LOCK_EX) === false) {
            throw new RuntimeException('installer lock 파일을 만들 수 없습니다: ' . $this->lockFile);
        }
    }
}
