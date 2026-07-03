<?php

declare(strict_types=1);

namespace MintWiki\Security;

/**
 * PHP 기본 세션 어댑터 skeleton (태스크 0633).
 *
 * 로그인 단계가 전역 $_SESSION에 직접 묶이지 않도록 최소한의 읽기/쓰기
 * 경계를 제공한다. 저장소 선택과 쿠키 보안 세부 정책은 후속 태스크에서
 * 확장한다.
 */
final class PhpSessionAdapter
{
    /**
     * PHP 세션을 시작한다.
     */
    public function start(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        if (!isset($_SESSION)) {
            $_SESSION = [];
        }
    }

    /**
     * 세션이 시작되었는지 확인한다.
     */
    public function isStarted(): bool
    {
        return session_status() === PHP_SESSION_ACTIVE;
    }

    /**
     * 세션 값을 읽는다.
     *
     * @param mixed $default 키가 없을 때 반환할 기본값
     * @return mixed 저장된 값 또는 기본값
     */
    public function get(string $key, mixed $default = null): mixed
    {
        $this->start();

        return $_SESSION[$key] ?? $default;
    }

    /**
     * 세션 값을 저장한다.
     *
     * @param mixed $value 저장할 값
     */
    public function set(string $key, mixed $value): void
    {
        $this->start();

        $_SESSION[$key] = $value;
    }

    /**
     * 세션 값을 제거한다.
     */
    public function remove(string $key): void
    {
        $this->start();

        unset($_SESSION[$key]);
    }

    /**
     * 현재 세션의 모든 값을 비운다.
     */
    public function clear(): void
    {
        $this->start();

        $_SESSION = [];
    }

    /**
     * 로그인 성공 시 사용할 세션 ID 재발급 진입점을 제공한다.
     */
    public function regenerateId(): bool
    {
        $this->start();

        return session_regenerate_id(true);
    }
}
