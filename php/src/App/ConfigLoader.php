<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 설정 로더 (태스크 0415).
 *
 * Python `src/app/config.py`의 `Settings`(pydantic-settings, `WIKI_` 접두어
 * 환경변수 + `.env` 파일)와 대응하는 PHP 쪽 설정 읽기 계약. 조회 우선순위는
 * 환경변수(`WIKI_` 접두어 + 대문자 key) → 생성자에 전달된 `$fileValues`
 * 배열 → `$default` 순이다. Python 쪽 pydantic-settings의
 * env-overrides-file 우선순위와 동일하다.
 *
 * 실제 파일에서 `$fileValues`를 읽는 로직(`.env`와 `local-config.php`)은
 * LocalConfigLoader(0616)에서 제공된다. entry point (index.php 등)에서
 * LocalConfigLoader로 파일 값을 읽고, 그것을 ConfigLoader의 생성자로
 * 전달하는 식으로 사용한다.
 *
 * @see LocalConfigLoader
 */
final class ConfigLoader
{
    private const ENV_PREFIX = 'WIKI_';

    /**
     * @param array<string, mixed> $fileValues config 파일에서 읽었다고
     *     가정하는 값들. 실제 파일 파싱은 이 태스크의 범위 밖이다.
     */
    public function __construct(
        private readonly array $fileValues = []
    ) {
    }

    public function get(string $key, mixed $default = null): mixed
    {
        $envValue = getenv(self::ENV_PREFIX . strtoupper($key));
        if ($envValue !== false) {
            return $envValue;
        }

        if (array_key_exists($key, $this->fileValues)) {
            return $this->fileValues[$key];
        }

        return $default;
    }
}
