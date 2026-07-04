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

    /**
     * docroot(`php/public`) 밖 비공개 위치(`php/config`)의 기본 lock 경로로
     * 인스턴스를 만든다 (태스크 0682). `config/local-config.php`와 마찬가지로
     * 웹에서 직접 접근할 수 없는 디렉터리이며, 이미 저장소에 존재해 별도
     * 디렉터리 생성 없이 바로 lock 파일을 기록할 수 있다.
     */
    public static function atDefaultPath(): self
    {
        return new self(dirname(__DIR__, 2) . '/config/' . self::DEFAULT_FILENAME);
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
