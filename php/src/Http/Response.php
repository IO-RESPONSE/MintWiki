<?php

declare(strict_types=1);

namespace MintWiki\Http;

/**
 * HTTP 응답을 표현하는 불변 value object (태스크 0395).
 *
 * status, headers, body 세 필드만 둔다 — 전송(front controller 연결)이나
 * 헤더 조작 헬퍼 등은 이후 태스크에서 필요할 때 추가한다.
 */
final class Response
{
    /**
     * @param array<string, string> $headers
     */
    public function __construct(
        private readonly int $status,
        private readonly array $headers = [],
        private readonly string $body = ''
    ) {
    }

    public function status(): int
    {
        return $this->status;
    }

    /**
     * @return array<string, string>
     */
    public function headers(): array
    {
        return $this->headers;
    }

    public function body(): string
    {
        return $this->body;
    }
}
