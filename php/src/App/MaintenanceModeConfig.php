<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 설정 기반 유지보수 모드 토글.
 *
 * `maintenance_mode` 설정 하나만 읽어 켜짐/꺼짐 여부를 판단한다.
 * 실제 HTTP 차단이나 page 연결은 별도 어댑터 계층에서 수행한다.
 */
final class MaintenanceModeConfig
{
    public function __construct(
        private readonly ConfigLoader $config
    ) {
    }

    public function isEnabled(): bool
    {
        return $this->toBoolean($this->config->get('maintenance_mode', false));
    }

    private function toBoolean(mixed $value): bool
    {
        if (is_bool($value)) {
            return $value;
        }

        if (is_int($value)) {
            return $value === 1;
        }

        if (!is_string($value)) {
            return false;
        }

        $normalized = strtolower(trim($value));

        return in_array($normalized, ['1', 'true', 'yes', 'on'], true);
    }
}
