<?php

declare(strict_types=1);

namespace MintWiki\Tests\Parser;

/**
 * `tests/modules/parser/fixtures/` 아래의 교차언어(cross-language) JSON
 * fixture(`docs/cross-language-fixture-schema.md`)를 읽어 parser 콜백을
 * 검증하는 러너. parser 모듈의 PHP 포팅은 아직 placeholder(0399)이므로,
 * 이 러너는 실제 `MintWiki\Parser` 클래스가 아니라 호출자가 넘기는 임의의
 * 콜백(`callable(string $source): array`)을 대상으로 동작한다 — 실 파서가
 * 준비되면 그 `parse()`를 그대로 넘길 수 있다.
 *
 * JSON 디코딩은 이 클래스가 직접 수행한다. 여러 모듈이 공유하는 fixture
 * 로더는 0425(Add PHP shared fixture loader)에서 별도로 추가되므로, 이
 * 러너를 그 로더의 대체물로 미리 일반화하지 않는다.
 */
final class FixtureRunner
{
    private string $fixtureDir;

    public function __construct(?string $fixtureDir = null)
    {
        $this->fixtureDir = $fixtureDir ?? dirname(__DIR__, 4) . '/tests/modules/parser/fixtures';
    }

    public function fixtureDir(): string
    {
        return $this->fixtureDir;
    }

    /**
     * @return list<string> 알파벳 순으로 정렬된 `.json` 픽스처 파일명 목록.
     */
    public function listFixtures(): array
    {
        $paths = glob($this->fixtureDir . '/*.json') ?: [];
        $names = array_map('basename', $paths);
        sort($names);

        return $names;
    }

    /**
     * @return array{schema_version:string,description?:string,input:mixed,expected:mixed,errors:array<int,string>}
     */
    public function loadFixture(string $filename): array
    {
        $path = $this->fixtureDir . '/' . $filename;

        if (!is_file($path)) {
            throw new \RuntimeException("Fixture 파일을 찾을 수 없습니다: {$path}");
        }

        $decoded = json_decode((string) file_get_contents($path), true);

        if (!is_array($decoded)) {
            throw new \RuntimeException("Fixture 파일이 올바른 JSON 객체가 아닙니다: {$path}");
        }

        return $decoded;
    }

    /**
     * 픽스처의 `input.source`를 `$parseFn`에 전달하고, 반환값을
     * `expected`와 비교한다. `$parseFn`은 `['blocks' => ..., 'metadata' => ...]`
     * 형태의 배열을 반환해야 한다(`docs/cross-language-fixture-schema.md`의
     * ParserResult 계약).
     *
     * @return array{success:bool,fixture:string,expected:mixed,actual:mixed}
     */
    public function run(string $filename, callable $parseFn): array
    {
        $fixture = $this->loadFixture($filename);
        $actual = $parseFn($fixture['input']['source']);
        $expected = $fixture['expected'];

        return [
            'success' => $actual === $expected,
            'fixture' => $filename,
            'expected' => $expected,
            'actual' => $actual,
        ];
    }
}
