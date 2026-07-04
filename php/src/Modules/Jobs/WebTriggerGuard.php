<?php

declare(strict_types=1);

namespace MintWiki\Jobs;

use InvalidArgumentException;

/**
 * 웹 요청으로 실행되는 잡 러너의 최소 접근 경계를 확인한다.
 *
 * 공유 호스팅에서는 cron/worker 대신 HTTP 엔드포인트로 잡 실행을 깨울 수
 * 있으므로, 고정 비밀 토큰과 짧은 윈도우의 시도 횟수 제한을 함께 적용한다.
 */
final class WebTriggerGuard
{
    private const DEFAULT_CLIENT_KEY = 'default';

    /** @var array<string, array{window_start: int, attempts: int}> */
    private array $buckets = [];

    /** @var callable(): int */
    private $clock;

    /**
     * @param callable(): int|null $clock 테스트에서 시간을 고정하기 위한 clock
     */
    public function __construct(
        private readonly string $secretToken,
        private readonly int $maxAttempts = 3,
        private readonly int $windowSeconds = 60,
        ?callable $clock = null
    ) {
        if ($secretToken === '') {
            throw new InvalidArgumentException('웹 잡 실행 토큰은 비어 있을 수 없습니다.');
        }

        if ($maxAttempts < 1) {
            throw new InvalidArgumentException('웹 잡 실행 시도 제한은 1 이상이어야 합니다.');
        }

        if ($windowSeconds < 1) {
            throw new InvalidArgumentException('웹 잡 실행 제한 윈도우는 1초 이상이어야 합니다.');
        }

        $this->clock = $clock ?? static fn (): int => time();
    }

    /**
     * 요청 토큰과 클라이언트별 rate limit을 확인한다.
     */
    public function allows(string $providedToken, string $clientKey = self::DEFAULT_CLIENT_KEY): bool
    {
        $bucketKey = $this->normalizeClientKey($clientKey);
        $now = ($this->clock)();
        $bucket = $this->bucketFor($bucketKey, $now);

        if ($bucket['attempts'] >= $this->maxAttempts) {
            return false;
        }

        $bucket['attempts']++;
        $this->buckets[$bucketKey] = $bucket;

        return hash_equals($this->secretToken, $providedToken);
    }

    private function normalizeClientKey(string $clientKey): string
    {
        $clientKey = trim($clientKey);

        if ($clientKey === '') {
            return self::DEFAULT_CLIENT_KEY;
        }

        return $clientKey;
    }

    /**
     * 현재 윈도우에 해당하는 버킷을 반환한다.
     *
     * @return array{window_start: int, attempts: int}
     */
    private function bucketFor(string $bucketKey, int $now): array
    {
        $bucket = $this->buckets[$bucketKey] ?? null;

        if ($bucket === null || $now - $bucket['window_start'] >= $this->windowSeconds) {
            return ['window_start' => $now, 'attempts' => 0];
        }

        return $bucket;
    }
}
