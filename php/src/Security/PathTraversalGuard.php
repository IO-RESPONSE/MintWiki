<?php

declare(strict_types=1);

namespace MintWiki\Security;

use InvalidArgumentException;

/**
 * 신뢰된 기준 디렉토리 밖으로 나가는 상대 경로를 차단한다.
 */
final class PathTraversalGuard
{
    /**
     * 기준 디렉토리 아래의 안전한 경로로 결합한다.
     *
     * @throws InvalidArgumentException 상대 경로가 기준 디렉토리 밖을 가리키는 경우
     */
    public function join(string $basePath, string $relativePath): string
    {
        $basePath = $this->normalizeBasePath($basePath);
        $segments = $this->safeSegments($relativePath);

        if ($segments === []) {
            return $basePath;
        }

        return $basePath . '/' . implode('/', $segments);
    }

    private function normalizeBasePath(string $basePath): string
    {
        $normalized = str_replace('\\', '/', trim($basePath));
        $normalized = rtrim($normalized, '/');

        if ($normalized === '') {
            throw new InvalidArgumentException('기준 경로는 비어 있을 수 없습니다.');
        }

        return $normalized;
    }

    /**
     * @return list<string>
     */
    private function safeSegments(string $relativePath): array
    {
        if (str_contains($relativePath, "\0")) {
            throw new InvalidArgumentException('경로에 NUL 바이트를 포함할 수 없습니다.');
        }

        $normalized = str_replace('\\', '/', trim($relativePath));

        if ($this->isAbsolutePath($normalized)) {
            throw new InvalidArgumentException('상대 경로만 허용됩니다.');
        }

        $segments = [];
        foreach (explode('/', $normalized) as $segment) {
            if ($segment === '') {
                continue;
            }

            if ($segment === '.' || $segment === '..') {
                throw new InvalidArgumentException('경로 순회 구간은 허용되지 않습니다.');
            }

            $segments[] = $segment;
        }

        return $segments;
    }

    private function isAbsolutePath(string $path): bool
    {
        if (str_starts_with($path, '/')) {
            return true;
        }

        if (preg_match('/^[A-Za-z]:/', $path) === 1) {
            return true;
        }

        return str_starts_with($path, '//');
    }
}
