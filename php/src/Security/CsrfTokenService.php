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
     * 세션을 시작하고(아직 시작되지 않았다면) 토큰 배열을 초기화한다.
     *
     * 0688 실 배포본 라이브 smoke test에서 발견: 이 메서드가 세션을 직접
     * 시작하지 않고 `$_SESSION`이 이미 있다고 가정했을 때는, 로그인/문서
     * 편집/설치 마법사 POST 핸들러가 `session_start()`를 호출하는 다른
     * 코드보다 먼저 `validate()`를 부르는 실제 HTTP 요청(별도 프로세스)에서
     * `$_SESSION`이 그 요청 안에서만 존재하는 임시 배열이 되어 토큰이 항상
     * "유효하지 않음"으로 판정됐다(CLI 테스트는 파일 하나에서
     * `session_start()`를 미리 호출해 두므로 이 문제를 드러내지 못했다).
     */
    private function initializeSession(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

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
