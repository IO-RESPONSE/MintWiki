<?php

declare(strict_types=1);

namespace MintWiki\Http;

use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;

/**
 * 문서 API route 등록 (태스크 0420, 0683).
 *
 * Python 쪽 문서 API(`src/modules/document/router.py`, `/api/documents`
 * prefix)와 대응하는 path를 등록한다. `Router`가 아직 동적 세그먼트
 * (`/{id}` 등, 0397)를 지원하지 않으므로, path 파라미터가 필요 없는 정적
 * 경로(목록 조회, 생성, title 조회)만 여기서 등록한다. `/api/documents/{id}`,
 * `/api/documents/{id}/revisions` 같은 동적 경로는 Router가 동적 세그먼트를
 * 지원하게 될 때 이어서 등록한다.
 *
 * 0683에서 `GET /api/documents/by-title`을 `Document\Service`(+ 주입된
 * `Repository`)로 연결했다 — 저장소가 주입되지 않은 경우(DB 미설정/오류
 * 상태, `public/index.php` 참고)는 503을 반환해 앱을 죽이지 않는다. 나머지
 * `/api/documents` 목록/생성 route는 여전히 placeholder(501)로 남는다.
 */
final class DocumentApiRoutes
{
    public static function register(Router $router, ?Repository $documentRepository = null): void
    {
        $router->register('GET', '/api/documents', self::notImplementedHandler());
        $router->register('POST', '/api/documents', self::notImplementedHandler());
        $router->register('GET', '/api/documents/by-title', self::byTitleHandler($documentRepository));
    }

    private static function byTitleHandler(?Repository $documentRepository): callable
    {
        return static function () use ($documentRepository): Response {
            if ($documentRepository === null) {
                return Response::json([
                    'error' => 'db_unavailable',
                    'message' => '데이터베이스가 설정되지 않아 문서를 조회할 수 없습니다.',
                ], 503);
            }

            $query = $_GET['q'] ?? '';
            $query = is_string($query) ? $query : '';

            $documentService = new Service($documentRepository);

            try {
                $document = $documentService->getByTitle($query);
            } catch (EmptyTitleError) {
                return Response::json([
                    'error' => 'invalid_query',
                    'message' => '검색어(q)를 입력하세요.',
                ], 400);
            }

            if ($document === null) {
                return Response::json([
                    'error' => 'not_found',
                    'message' => '문서를 찾을 수 없습니다.',
                ], 404);
            }

            return Response::json([
                'id' => $document->id(),
                'title' => $document->title(),
                'normalizedTitle' => $document->normalizedTitle(),
                'currentRevisionId' => $document->currentRevisionId(),
            ]);
        };
    }

    private static function notImplementedHandler(): callable
    {
        return static fn (): Response => Response::json([
            'error' => 'not_implemented',
        ], 501);
    }
}
