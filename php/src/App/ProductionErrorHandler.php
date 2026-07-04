<?php

declare(strict_types=1);

namespace MintWiki\App;

use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Ui\ErrorPage;
use Throwable;

/**
 * Production 오류 응답을 만드는 handler 골격.
 *
 * debug=false 기준으로 원본 예외 메시지나 trace를 사용자 응답에 노출하지
 * 않는다. 실제 front controller 연결과 logger adapter 연결은 후속 작업에서
 * 수행한다.
 */
final class ProductionErrorHandler
{
    private const INTERNAL_ERROR_CODE = 'app.internal_error';
    private const INTERNAL_ERROR_MESSAGE = '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';

    public function __construct(
        private readonly ?ErrorPage $errorPage = null
    ) {
    }

    /**
     * 처리되지 않은 예외를 안전한 500 응답으로 변환한다.
     */
    public function handle(Throwable $exception, Request $request, ?string $requestId = null): Response
    {
        unset($exception);

        $resolvedRequestId = $requestId ?? $this->newRequestId();

        if ($this->wantsJson($request)) {
            return Response::json([
                'error' => [
                    'code' => self::INTERNAL_ERROR_CODE,
                    'message' => self::INTERNAL_ERROR_MESSAGE,
                    'request_id' => $resolvedRequestId,
                ],
            ], 500, ['X-Request-Id' => $resolvedRequestId]);
        }

        $page = $this->errorPage ?? new ErrorPage();

        return Response::html(
            $page->renderServerError(),
            500,
            ['X-Request-Id' => $resolvedRequestId]
        );
    }

    /**
     * API 경로와 JSON Accept 헤더는 JSON 오류 응답으로 처리한다.
     */
    private function wantsJson(Request $request): bool
    {
        if (str_starts_with($request->path(), '/api/')) {
            return true;
        }

        foreach ($request->headers() as $name => $value) {
            if (strtolower($name) === 'accept' && str_contains(strtolower($value), 'application/json')) {
                return true;
            }
        }

        return false;
    }

    private function newRequestId(): string
    {
        return 'req_' . bin2hex(random_bytes(8));
    }
}
