<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use RuntimeException;

/**
 * 설치 프로세스에서 시스템 요구사항을 검사하는 클래스.
 *
 * PHP 확장 모듈 availability 및 필수 디렉터리의 쓰기 권한을 확인한다.
 */
final class RequirementCheck
{
    /**
     * 기본 필수 PHP 확장 목록.
     *
     * @var array<string>
     */
    private const DEFAULT_REQUIRED_EXTENSIONS = ['pdo', 'json'];

    /**
     * 필수 PHP 확장 모듈 목록.
     *
     * @var array<string>
     */
    private array $requiredExtensions;

    /**
     * 필수 쓰기 가능 디렉터리 목록.
     *
     * @var array<string>
     */
    private array $requiredWritableDirs;

    /**
     * 초기화.
     *
     * @param array<string>|null $requiredExtensions 필수 PHP 확장 목록. null이면 기본값 사용.
     * @param array<string>|null $requiredWritableDirs 필수 쓰기 가능 디렉터리 목록.
     */
    public function __construct(?array $requiredExtensions = null, ?array $requiredWritableDirs = null)
    {
        $this->requiredExtensions = $requiredExtensions ?? self::DEFAULT_REQUIRED_EXTENSIONS;
        $this->requiredWritableDirs = $requiredWritableDirs ?? [];
    }

    /**
     * 모든 필수 PHP 확장이 설치되어 있는지 확인한다.
     *
     * @return bool 모든 필수 확장이 있으면 true.
     *
     * @throws RuntimeException 필수 확장이 없으면.
     */
    public function areRequiredExtensionsLoaded(): bool
    {
        $missingExtensions = [];

        foreach ($this->requiredExtensions as $extension) {
            if (!extension_loaded($extension)) {
                $missingExtensions[] = $extension;
            }
        }

        if ($missingExtensions !== []) {
            throw new RuntimeException('필수 PHP 확장이 없습니다: ' . implode(', ', $missingExtensions));
        }

        return true;
    }

    /**
     * 모든 필수 디렉터리가 쓰기 가능한지 확인한다.
     *
     * @return bool 모든 필수 디렉터리가 쓰기 가능하면 true.
     *
     * @throws RuntimeException 쓰기 불가능한 디렉터리가 있으면.
     */
    public function areRequiredDirectoriesWritable(): bool
    {
        $this->assertDirectoriesWritable($this->requiredWritableDirs);

        return true;
    }

    /**
     * 캐시 디렉터리가 쓰기 가능한지 확인한다.
     *
     * @return bool 캐시 디렉터리가 쓰기 가능하면 true.
     *
     * @throws RuntimeException 캐시 디렉터리가 없거나 쓰기 불가능하면.
     */
    public function isCacheDirectoryWritable(string $cacheDir): bool
    {
        $this->assertDirectoriesWritable([$cacheDir]);

        return true;
    }

    /**
     * 업로드 디렉터리가 쓰기 가능한지 확인한다.
     *
     * @return bool 업로드 디렉터리가 쓰기 가능하면 true.
     *
     * @throws RuntimeException 업로드 디렉터리가 없거나 쓰기 불가능하면.
     */
    public function isUploadDirectoryWritable(string $uploadDir): bool
    {
        $this->assertDirectoriesWritable([$uploadDir]);

        return true;
    }

    /**
     * 로그 디렉터리가 쓰기 가능한지 확인한다.
     *
     * @return bool 로그 디렉터리가 쓰기 가능하면 true.
     *
     * @throws RuntimeException 로그 디렉터리가 없거나 쓰기 불가능하면.
     */
    public function isLogDirectoryWritable(string $logDir): bool
    {
        $this->assertDirectoriesWritable([$logDir]);

        return true;
    }

    /**
     * 주어진 디렉터리 목록이 모두 쓰기 가능한지 확인한다.
     *
     * @param array<string> $dirs 쓰기 가능해야 하는 디렉터리 목록.
     *
     * @throws RuntimeException 쓰기 불가능한 디렉터리가 있으면.
     */
    private function assertDirectoriesWritable(array $dirs): void
    {
        $nonWritableDirs = [];

        foreach ($dirs as $dir) {
            if (!is_dir($dir)) {
                $nonWritableDirs[] = $dir . ' (존재하지 않음)';
            } elseif (!is_writable($dir)) {
                $nonWritableDirs[] = $dir . ' (쓰기 불가)';
            }
        }

        if ($nonWritableDirs !== []) {
            throw new RuntimeException('쓰기 불가능한 디렉터리가 있습니다: ' . implode(', ', $nonWritableDirs));
        }
    }
}
