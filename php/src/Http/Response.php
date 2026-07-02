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

    /**
     * 데이터를 JSON으로 인코딩하고 Content-Type 헤더를 채운 Response를 생성한다
     * (태스크 0417). 인코딩 실패 시 JsonException을 던진다 — 호출자가 직접
     * 처리하지 않아도 되도록 JSON_THROW_ON_ERROR를 사용한다.
     *
     * @param array<string, string> $headers 기본 Content-Type 헤더에 병합할 추가 헤더
     */
    public static function json(mixed $data, int $status = 200, array $headers = []): self
    {
        $body = json_encode($data, JSON_THROW_ON_ERROR);

        return new self($status, ['Content-Type' => 'application/json'] + $headers, $body);
    }
}
