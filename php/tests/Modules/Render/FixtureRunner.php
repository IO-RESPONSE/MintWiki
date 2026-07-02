<?php

declare(strict_types=1);

namespace MintWiki\Tests\Render;

/**
 * `tests/modules/render/fixtures/` 아래의 교차언어(cross-language) JSON
 * fixture(`docs/cross-language-fixture-schema.md`)를 읽어 render 콜백을
 * 검증하는 러너. render 모듈의 PHP 포팅은 아직 placeholder(0399)이므로,
 * 이 러너는 실제 `MintWiki\Render` 함수가 아니라 호출자가 넘기는 임의의
 * 콜백(`callable(array $input): mixed`)을 대상으로 동작한다 — 실 render
 * 함수가 준비되면 그 함수를 그대로 넘길 수 있다.
 *
 * parser fixture와 달리 render fixture는 `escape_html`/`sanitize_url`/
 * `render_heading` 등 함수마다 `input`의 형태(문자열 하나, `{level,
 * content}` 등)와 `expected`의 키(`html`/`url`/`value`/`id`)가 다르므로,
 * 이 러너는 `input.source`처럼 특정 키를 미리 꺼내지 않고 `input` 객체
 * 전체를 콜백에 그대로 넘긴다 — 어떤 키를 쓸지는 콜백(호출자)이 안다.
 * JSON 디코딩은 이 클래스가 직접 수행한다. 여러 모듈이 공유하는 fixture
 * 로더는 0425(Add PHP shared fixture loader)에서 별도로 추가되므로, 이
 * 러너를 그 로더의 대체물로 미리 일반화하지 않는다.
 */
final class FixtureRunner
{
    private string $fixtureDir;

    public function __construct(?string $fixtureDir = null)
    {
        $this->fixtureDir = $fixtureDir ?? dirname(__DIR__, 4) . '/tests/modules/render/fixtures';
    }

    public function fixtureDir(): string
    {
        return $this->fixtureDir;
    }

    /**
     * @return list<string> 알파벳 순으로 정렬된 `.json` 픽스처 파일명 목록.
     *     같은 디렉터리의 `.html` 스냅샷 픽스처(0372 이전부터 존재)는
     *     glob 패턴에서 제외되므로 포함되지 않는다.
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
     * 픽스처의 `input` 전체를 `$renderFn`에 전달하고, 반환값을 `expected`와
     * 비교한다. `$renderFn`은 fixture 파일명이 가리키는 render 함수(예:
     * `escape_html`, `render_heading`)가 기대하는 필드를 `$input`에서
     * 직접 꺼내 써야 한다.
     *
     * @return array{success:bool,fixture:string,expected:mixed,actual:mixed}
     */
    public function run(string $filename, callable $renderFn): array
    {
        $fixture = $this->loadFixture($filename);
        $actual = $renderFn($fixture['input']);
        $expected = $fixture['expected'];

        return [
            'success' => $actual === $expected,
            'fixture' => $filename,
            'expected' => $expected,
            'actual' => $actual,
        ];
    }
}
