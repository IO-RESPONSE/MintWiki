<?php

declare(strict_types=1);

namespace MintWiki\Security;

/**
 * CSRF 토큰 서비스 (태스크 0540).
 *
 * CSRF 토큰을 생성하고 검증한다. 토큰은 세션에 저장되며, 폼 제출 시
 * 검증되어 CSRF 공격을 방지한다.
 */
final class CsrfTokenService
{
    private const SESSION_KEY = 'csrf_tokens';
    private const TOKEN_LENGTH = 32;

    /**
     * 새로운 CSRF 토큰을 생성하고 세션에 저장한다.
     *
     * @return string 생성된 토큰
     */
    public function generate(): string
    {
        $this->initializeSession();

        $token = $this->generateRandomToken();
        $_SESSION[self::SESSION_KEY][$token] = true;

        return $token;
    }

    /**
     * CSRF 토큰을 검증한다.
     *
     * 토큰이 세션에 존재하면 검증 성공으로 간주하고, 사용 후 제거한다.
     *
     * @param string $token 검증할 토큰
     * @return bool 토큰이 유효하면 true, 그렇지 않으면 false
     */
    public function validate(string $token): bool
    {
        $this->initializeSession();

        if (!isset($_SESSION[self::SESSION_KEY][$token])) {
            return false;
        }

        unset($_SESSION[self::SESSION_KEY][$token]);

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
     * 크립토그래피로 안전한 무작위 토큰을 생성한다.
     *
     * @return string 16진수 문자열 토큰
     */
    private function generateRandomToken(): string
    {
        $bytes = random_bytes(self::TOKEN_LENGTH);
        return bin2hex($bytes);
    }
}
