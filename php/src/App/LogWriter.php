<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 애플리케이션 로그 기록 계약.
 *
 * 실제 오류 처리기와 운영 이벤트 연결은 후속 태스크에서 수행한다.
 */
interface LogWriter
{
    /**
     * @param array<string, mixed> $context 로그에 함께 남길 부가 정보
     */
    public function write(string $level, string $message, array $context = []): void;
}
