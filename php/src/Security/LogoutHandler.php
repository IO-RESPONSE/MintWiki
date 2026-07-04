<?php

declare(strict_types=1);

namespace MintWiki\Security;

use MintWiki\Http\Response;

/**
 * `GET`/`POST /logout` 요청을 처리한다 (태스크 0686).
 *
 * 세션을 완전히 비우고(`PhpSessionAdapter::clear()`) 세션 ID를 재발급한 뒤
 * 홈으로 리다이렉트한다. 이미 로그아웃 상태에서 호출해도 오류 없이 동일하게
 * 동작한다.
 */
final class LogoutHandler
{
    private PhpSessionAdapter $sessionAdapter;

    public function __construct(?PhpSessionAdapter $sessionAdapter = null)
    {
        $this->sessionAdapter = $sessionAdapter ?? new PhpSessionAdapter();
    }

    public function handle(): Response
    {
        $this->sessionAdapter->clear();
        $this->sessionAdapter->regenerateId();

        return new Response(302, ['Location' => '/']);
    }
}
