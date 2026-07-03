<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * 인증 route 등록 (태스크 0565).
 *
 * 로그인/로그아웃 route들을 등록한다. 모든 route는 501을 반환하는
 * placeholder 핸들러다. 실제 로직 연결은 이후 태스크에서 이루어진다.
 */
final class AuthRoutes
{
    public static function register(Router $router): void
    {
        $router->register('GET', '/login', self::notImplementedHandler());
        $router->register('POST', '/login', self::notImplementedHandler());
        $router->register('POST', '/logout', self::notImplementedHandler());
    }

    private static function notImplementedHandler(): callable
    {
        return static fn (): Response => Response::json([
            'error' => 'not_implemented',
        ], 501);
    }
}
