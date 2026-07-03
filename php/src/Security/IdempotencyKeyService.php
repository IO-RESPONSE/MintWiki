<?php

declare(strict_types=1);

namespace MintWiki\Security;

/**
 * 중복 제출 방지를 위한 Idempotency Key 서비스 (태스크 0569).
 *
 * Idempotency key를 생성하고 검증한다. 키는 세션에 저장되며, 폼 제출 시
 * 검증되어 중복 제출을 방지한다. 한 번 사용된 키는 재사용할 수 없다.
 */
final class IdempotencyKeyService
{
    private const SESSION_KEY = 'idempotency_keys';
    private const KEY_LENGTH = 32;

    /**
     * 새로운 idempotency key를 생성하고 세션에 저장한다.
     *
     * @return string 생성된 키
     */
    public function generate(): string
    {
        $this->initializeSession();

        $key = $this->generateRandomKey();
        $_SESSION[self::SESSION_KEY][$key] = true;

        return $key;
    }

    /**
     * Idempotency key를 검증한다.
     *
     * 키가 세션에 존재하면 검증 성공으로 간주하고, 사용 후 제거한다.
     * 이를 통해 같은 키로 중복 제출되는 것을 방지한다.
     *
     * @param string $key 검증할 키
     * @return bool 키가 유효하면 true, 그렇지 않으면 false
     */
    public function validate(string $key): bool
    {
        $this->initializeSession();

        if (!isset($_SESSION[self::SESSION_KEY][$key])) {
            return false;
        }

        unset($_SESSION[self::SESSION_KEY][$key]);

        return true;
    }

    /**
     * 세션 배열을 초기화한다.
     */
    private function initializeSession(): void
    {
        if (!isset($_SESSION[self::SESSION_KEY])) {
            $_SESSION[self::SESSION_KEY] = [];
        }
    }

    /**
     * 크립토그래피로 안전한 무작위 키를 생성한다.
     *
     * @return string 16진수 문자열 키
     */
    private function generateRandomKey(): string
    {
        $bytes = random_bytes(self::KEY_LENGTH);
        return bin2hex($bytes);
    }
}
