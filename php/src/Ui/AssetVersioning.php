<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 정적 asset URL에 캐시 무효화용 버전 쿼리 매개변수를 추가한다.
 *
 * 파일의 SHA-256 해시를 계산하여 URL 쿼리 매개변수로 추가한다.
 * 예: /assets/css/design-tokens.css → /assets/css/design-tokens.css?v=abc123de
 */
final class AssetVersioning
{
    /**
     * @param string $assetBasePath asset 파일의 기본 경로. 기본값은 공개 디렉토리.
     */
    public function __construct(
        private readonly string $assetBasePath = __DIR__ . '/../../public'
    ) {
    }

    /**
     * asset URL에 해시 쿼리 매개변수를 추가한다.
     *
     * @param string $path URL 경로 (예: /assets/css/design-tokens.css)
     * @return string 해시 쿼리를 포함한 URL
     * @throws \RuntimeException 파일을 읽을 수 없는 경우
     */
    public function url(string $path): string
    {
        // 경로 검증: /assets로 시작해야 함
        if (!str_starts_with($path, '/assets/')) {
            throw new \RuntimeException("Asset 경로는 '/assets/'로 시작해야 합니다: {$path}");
        }

        // 절대 경로 구성
        $filePath = $this->assetBasePath . $path;

        // 경로 정규화 및 순회 공격 방지
        $baseRealPath = realpath($this->assetBasePath);
        if ($baseRealPath === false) {
            throw new \RuntimeException("Asset 기본 경로가 유효하지 않습니다");
        }

        // 심볼릭 링크 및 `..` 등을 해결하려고 realpath를 호출하되,
        // 파일이 없으면 dirname의 realpath로 부모 디렉토리 검증
        if (is_file($filePath)) {
            $realPath = realpath($filePath);
        } else {
            // 파일이 없는 경우, 부모 디렉토리의 realpath로 경로 검증
            $dirPath = dirname($filePath);
            $realDir = realpath($dirPath);
            if ($realDir === false) {
                throw new \RuntimeException("Asset 경로가 유효하지 않습니다: {$path}");
            }
            $realPath = $realDir . '/' . basename($filePath);
        }

        // 경로 순회 공격 방지: realPath가 baseRealPath 아래에 있는지 확인
        if (!str_starts_with($realPath, $baseRealPath . '/') && $realPath !== $baseRealPath) {
            throw new \RuntimeException("Asset 경로가 유효하지 않습니다: {$path}");
        }

        // 파일 존재 여부 확인
        if (!is_file($filePath)) {
            throw new \RuntimeException("Asset 파일을 찾을 수 없습니다: {$path}");
        }

        // 파일 내용 읽기 및 해시 계산
        $contents = file_get_contents($filePath);
        if ($contents === false) {
            throw new \RuntimeException("Asset 파일을 읽을 수 없습니다: {$path}");
        }

        $hash = substr(hash('sha256', $contents), 0, 8);

        return $path . '?v=' . $hash;
    }
}
