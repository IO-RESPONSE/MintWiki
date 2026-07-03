<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 런타임 저장소 경로 설정.
 *
 * 공유 호스팅마다 프로젝트 루트와 쓰기 가능 디렉터리 위치가 다를 수 있으므로
 * `storage_path` 설정 하나에서 하위 저장소 경로를 일관되게 계산한다.
 */
final class StoragePathConfig
{
    private string $defaultStoragePath;

    public function __construct(
        private readonly ConfigLoader $config,
        ?string $defaultStoragePath = null
    ) {
        $this->defaultStoragePath = $this->normalizePath(
            $defaultStoragePath ?? dirname(__DIR__, 2) . '/storage'
        );
    }

    public function rootPath(): string
    {
        $configuredPath = $this->config->get('storage_path');

        if (is_string($configuredPath) && trim($configuredPath) !== '') {
            return $this->normalizePath($configuredPath);
        }

        return $this->defaultStoragePath;
    }

    public function cachePath(): string
    {
        return $this->rootPath() . '/cache';
    }

    public function uploadsPath(): string
    {
        return $this->rootPath() . '/uploads';
    }

    public function logsPath(): string
    {
        return $this->rootPath() . '/logs';
    }

    private function normalizePath(string $path): string
    {
        $normalized = rtrim($path, "/\\");

        if ($normalized === '') {
            return '/';
        }

        return $normalized;
    }
}
