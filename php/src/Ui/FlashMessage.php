<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 플래시 메시지 서비스 (태스크 0543).
 *
 * 리다이렉트 후 일회성 메시지를 표시하기 위해 세션에 메시지를 저장하고 검색한다.
 * 메시지는 검색 후 자동으로 세션에서 제거된다.
 */
final class FlashMessage
{
    private const SESSION_KEY = 'flash_message';

    /**
     * 플래시 메시지를 세션에 저장한다.
     *
     * @param string $message 저장할 메시지
     * @param string $type 메시지 타입 (success, warning, error, info)
     */
    public function set(string $message, string $type = 'success'): void
    {
        $this->initializeSession();
        $_SESSION[self::SESSION_KEY] = [
            'message' => $message,
            'type' => $type,
        ];
    }

    /**
     * 플래시 메시지를 세션에서 검색하고 제거한다.
     *
     * @return array<string, string>|null 메시지 배열 (message, type 포함) 또는 null
     */
    public function get(): ?array
    {
        $this->initializeSession();

        if (!isset($_SESSION[self::SESSION_KEY])) {
            return null;
        }

        $message = $_SESSION[self::SESSION_KEY];
        unset($_SESSION[self::SESSION_KEY]);

        return $message;
    }

    /**
     * 세션 배열을 초기화한다.
     */
    private function initializeSession(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        if (!isset($_SESSION)) {
            $_SESSION = [];
        }
    }
}
