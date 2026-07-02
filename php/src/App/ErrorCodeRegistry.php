<?php

declare(strict_types=1);

namespace MintWiki\App;

use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\NotFoundError as DocumentNotFoundError;

/**
 * PHP 쪽 안정적인 error code 중앙 registry (태스크 0416).
 *
 * `docs/portable-exception-code-policy.md`가 고정한 `<module>.<reason>`
 * 형식 검증과, 이미 선언된 code 값들의 조회를 한 곳에서 제공한다. code
 * 문자열 자체의 정본은 여전히 각 모듈 예외 클래스의 `CODE` 상수다 — 이
 * registry는 그 상수들을 참조만 할 뿐 값을 따로 복사해 하드코딩하지
 * 않는다. 그래서 상수 값이 바뀌면(있어서는 안 되지만) 이 목록도 함께
 * 갱신된다.
 *
 * Python 쪽에는 `code` class attribute를 노출하는 예외 클래스만 있고
 * 이를 모아 놓은 별도 registry 모듈은 없다(`tests/modules/document/
 * test_error_codes.py`가 개별 클래스에서 직접 모아 검증한다). 이 클래스는
 * 그 검증 방식을 PHP 쪽에서 재사용 가능한 형태로 옮긴 것이며, 등록된 code
 * 이름은 Python 쪽 값과 문자 그대로 같다(`docs/portable-exception-code-
 * policy.md`의 Notes: "Python error code와 이름을 맞춘다").
 */
final class ErrorCodeRegistry
{
    private const CODE_PATTERN = '/^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$/';

    /**
     * 현재 PHP 쪽에 선언된 모든 안정적인 error code 목록. 새 모듈이 code를
     * 얻으면(Python 쪽에 먼저 `code`가 생긴 뒤) 여기에 그 클래스의 `CODE`
     * 상수를 추가한다.
     *
     * @var list<string>
     */
    private const KNOWN_CODES = [
        EmptyTitleError::CODE,
        DuplicateNormalizedTitleError::CODE,
        DocumentNotFoundError::CODE,
    ];

    /**
     * @return list<string> 등록된 모든 error code
     */
    public static function all(): array
    {
        return self::KNOWN_CODES;
    }

    /**
     * 주어진 code가 registry에 등록되어 있는지 확인한다.
     */
    public static function has(string $code): bool
    {
        return in_array($code, self::KNOWN_CODES, true);
    }

    /**
     * `<module>.<reason>` 형식(소문자 snake_case, 점 하나로 구분)을
     * 따르는지 확인한다. 형식 자체는 `docs/portable-exception-code-
     * policy.md`의 "Code 형식" 절이 정의한다.
     */
    public static function isValidFormat(string $code): bool
    {
        return preg_match(self::CODE_PATTERN, $code) === 1;
    }
}
