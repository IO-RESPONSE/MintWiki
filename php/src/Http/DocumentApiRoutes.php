<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * 문서 API placeholder route 등록 (태스크 0420).
 *
 * Python 쪽 문서 API(`src/modules/document/router.py`, `/api/documents`
 * prefix)와 대응하는 path를 아직 저장소/서비스 연결 없이 미리 예약해 둔다
 * — 모든 route는 501을 반환하는 placeholder 핸들러다. `Router`가 아직
 * 동적 세그먼트(`/{id}` 등, 0397)를 지원하지 않으므로, path 파라미터가
 * 필요 없는 정적 경로(목록 조회, 생성, title 조회)만 여기서 등록한다.
 * `/api/documents/{id}`, `/api/documents/{id}/revisions` 같은 동적 경로는
 * Router가 동적 세그먼트를 지원하게 될 때 이어서 등록한다.
 */
final class DocumentApiRoutes
{
    public static function register(Router $router): void
    {
        $router->register('GET', '/api/documents', self::notImplementedHandler());
        $router->register('POST', '/api/documents', self::notImplementedHandler());
        $router->register('GET', '/api/documents/by-title', self::notImplementedHandler());
    }

    private static function notImplementedHandler(): callable
    {
        return static fn (): Response => Response::json([
            'error' => 'not_implemented',
        ], 501);
    }
}
