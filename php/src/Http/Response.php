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
        private readonly string $body = '',
        private readonly ?string $streamFilePath = null
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
     * 전송 시점에 `readfile()`로 스트리밍해야 할 파일 경로 (태스크 0716).
     *
     * body 문자열에 파일 전체를 담지 않고 경로만 보관해, 대용량 백업
     * 파일도 메모리에 통째로 올리지 않고 내려받게 한다. 일반 응답은
     * null을 반환한다.
     */
    public function streamFilePath(): ?string
    {
        return $this->streamFilePath;
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

    /**
     * HTML 문자열을 body로 하고 Content-Type 헤더를 채운 Response를 생성한다
     * (태스크 0418). 서버 렌더링 기반만 두는 단계이므로 이스케이프나 템플릿
     * 처리는 하지 않고, 이미 완성된 HTML 문자열을 그대로 감싼다.
     *
     * 태스크 0554에서 보안 헤더(CSP, nosniff, frame options)를 추가했다.
     * 태스크 0577에서 캐시 정책 헤더(Cache-Control)를 추가했다.
     *
     * @param array<string, string> $headers 기본 헤더들에 병합할 추가 헤더
     */
    public static function html(string $body, int $status = 200, array $headers = []): self
    {
        $defaultHeaders = [
            'Content-Type' => 'text/html; charset=utf-8',
            'Cache-Control' => 'no-cache, no-store, must-revalidate',
            'X-Content-Type-Options' => 'nosniff',
            'X-Frame-Options' => 'DENY',
            'Content-Security-Policy' => "default-src 'self'",
        ];

        return new self($status, $defaultHeaders + $headers, $body);
    }

    /**
     * 정적 자산(CSS, JS, 이미지 등)을 body로 하고 적절한 캐시 헤더를 설정한
     * Response를 생성한다 (태스크 0578).
     *
     * 캐시 정책은 파일명에 hash가 포함되어 있는지 여부에 따라 달라진다:
     * - hash가 있는 파일(예: app.abc123def456.js): 1년 캐시, immutable
     * - hash가 없는 파일(예: responsive-table.css): 1시간 캐시
     *
     * @param string $contentType Content-Type 헤더 값 (예: 'text/css', 'application/javascript')
     * @param string $body 파일 내용
     * @param string $filename 캐시 정책 결정에 사용할 파일명 (hash 감지용)
     * @param array<string, string> $headers 기본 헤더들에 병합할 추가 헤더
     */
    public static function staticAsset(string $contentType, string $body, string $filename = '', int $status = 200, array $headers = []): self
    {
        // 파일명에서 hash 여부를 판단한다. hash는 일반적으로 점으로 구분된
        // 중간 세그먼트로 나타난다 (예: app.abc123def456.js에서 abc123def456).
        $hasHash = self::hasHashInFilename($filename);

        if ($hasHash) {
            // hash가 있는 파일은 1년 동안 캐시하고 재검증하지 않는다
            $cacheControl = 'public, max-age=31536000, immutable';
        } else {
            // hash가 없는 파일은 1시간 동안 캐시한다
            $cacheControl = 'public, max-age=3600';
        }

        $defaultHeaders = [
            'Content-Type' => $contentType,
            'Cache-Control' => $cacheControl,
        ];

        return new self($status, $defaultHeaders + $headers, $body);
    }

    /**
     * 파일을 첨부(attachment) 다운로드로 내려보내는 Response를 생성한다
     * (태스크 0716). body는 비워두고 파일 경로만 담아, 실제 전송은
     * `mintwiki_send_response()`가 `readfile()`로 스트리밍하게 한다.
     *
     * @param array<string, string> $headers 기본 헤더들에 병합할 추가 헤더
     */
    public static function download(string $filePath, string $downloadFilename, string $contentType, int $contentLength, array $headers = []): self
    {
        $safeFilename = str_replace(['"', "\r", "\n"], '', $downloadFilename);

        $defaultHeaders = [
            'Content-Type' => $contentType,
            'Content-Disposition' => 'attachment; filename="' . $safeFilename . '"',
            'Content-Length' => (string) $contentLength,
            'X-Content-Type-Options' => 'nosniff',
        ];

        return new self(200, $defaultHeaders + $headers, '', $filePath);
    }

    /**
     * 파일명에 hash가 포함되어 있는지 확인한다.
     *
     * hash는 일반적으로 점으로 구분된 중간 세그먼트로 나타난다.
     * 예: app.abc123def456.js의 경우 abc123def456 부분을 감지한다.
     */
    private static function hasHashInFilename(string $filename): bool
    {
        // 파일명이 비어있으면 hash가 없는 것으로 간주한다
        if (empty($filename)) {
            return false;
        }

        // 점으로 분리된 부분들을 추출한다
        $parts = explode('.', $filename);

        // 파일명이 name.hash.ext 형태여야 hash가 있다고 본다
        if (count($parts) < 3) {
            return false;
        }

        // 중간 세그먼트(hash 위치)를 확인한다
        // hash는 일반적으로 6자 이상의 문자(대소문자, 숫자만 포함)다
        $middleSegments = array_slice($parts, 1, -1);
        foreach ($middleSegments as $segment) {
            if (strlen($segment) >= 6 && ctype_alnum($segment)) {
                return true;
            }
        }

        return false;
    }
}
