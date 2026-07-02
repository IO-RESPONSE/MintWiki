<?php

declare(strict_types=1);

namespace MintWiki\Tests\Support;

/**
 * 저장소 루트의 `tests/modules/<module>/fixtures/`, `tests/fixtures/`
 * (`docs/fixture-directory-convention.md`) 아래에 있는 교차언어
 * (cross-language) JSON fixture(`docs/cross-language-fixture-schema.md`)를
 * 읽는 공용 헬퍼. `Modules/Parser/FixtureRunner.php`, `Modules/Render/
 * FixtureRunner.php`가 각자 반복 정의한 `json_decode` 로직을 한 곳으로
 * 모아, 이후 모듈별 parity 테스트(`docs/php-parity-test-plan.md`의 0426+
 * 계획)가 재사용할 수 있게 한다. 기존 두 FixtureRunner는 이 태스크
 * 이전부터 각자의 로직을 유지하고 있으므로, 이 로더는 그것들을
 * 대체하지 않고 새 재사용 지점으로만 추가된다.
 */
final class FixtureLoader
{
    private string $repositoryRoot;

    public function __construct(?string $repositoryRoot = null)
    {
        $this->repositoryRoot = $repositoryRoot ?? dirname(__DIR__, 3);
    }

    public function repositoryRoot(): string
    {
        return $this->repositoryRoot;
    }

    /**
     * 모듈 전용 fixture 디렉터리 경로: `tests/modules/<module>/fixtures/`.
     */
    public function moduleFixtureDir(string $module): string
    {
        return $this->repositoryRoot . '/tests/modules/' . $module . '/fixtures';
    }

    /**
     * 여러 모듈이 함께 참조하는 공유 fixture 디렉터리 경로: `tests/fixtures/`.
     */
    public function sharedFixtureDir(): string
    {
        return $this->repositoryRoot . '/tests/fixtures';
    }

    /**
     * `$dir` 아래 `.json` 파일명을 알파벳 순으로 정렬해 반환한다.
     *
     * @return list<string>
     */
    public function listFixtures(string $dir): array
    {
        $paths = glob($dir . '/*.json') ?: [];
        $names = array_map('basename', $paths);
        sort($names);

        return $names;
    }

    /**
     * `$dir/$filename`을 읽어 JSON을 배열로 디코드한다.
     *
     * @return array{schema_version:string,description?:string,input:mixed,expected:mixed,errors:array<int,string>}
     */
    public function loadFixture(string $dir, string $filename): array
    {
        $path = $dir . '/' . $filename;

        if (!is_file($path)) {
            throw new \RuntimeException("Fixture 파일을 찾을 수 없습니다: {$path}");
        }

        $decoded = json_decode((string) file_get_contents($path), true);

        if (!is_array($decoded)) {
            throw new \RuntimeException("Fixture 파일이 올바른 JSON 객체가 아닙니다: {$path}");
        }

        return $decoded;
    }
}
