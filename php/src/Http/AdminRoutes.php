<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * 관리자 route 등록 (태스크 0564).
 *
 * 관리자 기능 route들을 등록한다: 대시보드, 상태 조회, 신고, 감사, 사용자 차단.
 * 모든 route는 501을 반환하는 placeholder 핸들러다. 실제 로직 연결은 이후
 * 태스크에서 이루어진다.
 */
final class AdminRoutes
{
    public static function register(Router $router): void
    {
        $router->register('GET', '/admin', self::notImplementedHandler());
        $router->register('GET', '/admin/status', self::notImplementedHandler());
        $router->register('GET', '/admin/reporting', self::notImplementedHandler());
        $router->register('GET', '/admin/audit', self::notImplementedHandler());
        $router->register('POST', '/admin/block-user', self::notImplementedHandler());
    }

    private static function notImplementedHandler(): callable
    {
        return static fn (): Response => Response::json([
            'error' => 'not_implemented',
        ], 501);
    }
}
