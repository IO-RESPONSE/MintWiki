<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * HTTP 요청을 표현하는 불변 value object (태스크 0396).
 *
 * method, path, query, body, headers 다섯 필드만 둔다 — 전역 서버 변수
 * ($_SERVER, $_GET 등)로부터의 생성이나 라우팅 연결은 이후 태스크
 * (0397 router skeleton, 0398 route 등록 테스트)에서 필요할 때 추가한다.
 */
final class Request
{
    /**
     * @param array<string, string> $query
     * @param array<string, string> $headers
     */
    public function __construct(
        private readonly string $method,
        private readonly string $path,
        private readonly array $query = [],
        private readonly string $body = '',
        private readonly array $headers = []
    ) {
    }

    public function method(): string
    {
        return $this->method;
    }

    public function path(): string
    {
        return $this->path;
    }

    /**
     * @return array<string, string>
     */
    public function query(): array
    {
        return $this->query;
    }

    public function body(): string
    {
        return $this->body;
    }

    /**
     * @return array<string, string>
     */
    public function headers(): array
    {
        return $this->headers;
    }
}
