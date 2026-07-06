<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 진단 값 export/preview에서 민감 정보로 보이는 항목을 제외하는 공용 필터
 * (태스크 0717).
 *
 * 원래 `MintWiki\Ui\OperationalDiagnosticsPage`에만 있던
 * isSensitiveEnvironmentKey/safeEnvironmentDiagnostics 로직을 그대로 옮겨
 * export route(JSON 다운로드)와 화면 preview가 같은 판정 기준을 공유하게
 * 했다. 판정은 값이 아니라 key 이름만 보고 이뤄지므로, DSN 자격(`database_url`
 * 처럼 값 안에 사용자명/비밀번호가 포함되는 key)까지 걸러내도록 `dsn`/`url`
 * 패턴을 추가했다 — `OperationalDiagnosticsCollector`의 export 스냅샷은
 * 애초에 그런 key를 담지 않지만, 이 필터가 마지막 방어선 역할을 한다.
 */
final class SensitiveDiagnosticsFilter
{
    private const SENSITIVE_KEY_PATTERN = '/(password|passwd|secret|token|credential|auth|cookie|session'
        . '|dsn|url|api[_-]?key|private[_-]?key|(^|[_-])key($|[_-]))/i';

    /**
     * 진단 값 map에서 민감한 key로 판정되는 항목을 제외한다.
     *
     * @param array<string, string> $diagnostics
     *
     * @return array<string, string>
     */
    public static function filter(array $diagnostics): array
    {
        $safeDiagnostics = [];

        foreach ($diagnostics as $key => $value) {
            if (self::isSensitiveKey($key)) {
                continue;
            }

            $safeDiagnostics[$key] = $value;
        }

        return $safeDiagnostics;
    }

    /**
     * 환경 변수/진단 key 이름만 보고 민감 정보 가능성이 큰 항목을 판정한다.
     */
    public static function isSensitiveKey(string $key): bool
    {
        return preg_match(self::SENSITIVE_KEY_PATTERN, $key) === 1;
    }
}
