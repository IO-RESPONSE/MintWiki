<?php

declare(strict_types=1);

namespace MintWiki\App;

use PDO;

/**
 * 운영 진단 page(`MintWiki\Ui\OperationalDiagnosticsPage`)와 환경 진단
 * export route가 함께 쓰는 실데이터 수집기 (태스크 0717).
 *
 * DB 연결(`AppBootstrap`이 이미 만든 `PDO`/연결 상태 문자열), 스키마
 * 버전(`schema_version` 테이블), 캐시 백엔드 설정(`ConfigLoader`의
 * `redis_url`, 없으면 `StoragePathConfig`의 파일 캐시 경로), 앱 버전/환경을
 * 조회한다. DB가 미설정/오류 상태(`$pdo === null`)이거나 스키마가 아직
 * 적용되지 않은 상태에서도 예외를 던지지 않고 "미설정"/"오류" 문자열로
 * 대체한다 — index.php의 0674 계약(치명적 오류로 죽지 않음)과 동일한
 * 판단이다.
 */
final class OperationalDiagnosticsCollector
{
    public function __construct(
        private readonly ?PDO $pdo,
        private readonly string $dbConnectionStatus,
        private readonly ConfigLoader $configLoader,
        private readonly StoragePathConfig $storagePathConfig,
        private readonly string $appVersion
    ) {
    }

    /**
     * 운영 진단 page 렌더링에 쓰이는 구조화된 진단 값을 반환한다.
     *
     * @return array{
     *     db: array{status: string, version: string},
     *     schema: array{status: string, migration: string},
     *     cache: array{status: string, usage: string},
     *     environment: array<string, string>
     * }
     */
    public function collect(): array
    {
        return [
            'db' => $this->collectDatabase(),
            'schema' => $this->collectSchema(),
            'cache' => $this->collectCache(),
            'environment' => $this->collectEnvironment(),
        ];
    }

    /**
     * 환경 진단 export(JSON 다운로드)에 담을 평면 스냅샷을 반환한다.
     *
     * DB 자격 증명(DSN/사용자명/비밀번호)은 애초에 조회하지 않으므로 이
     * 스냅샷에는 절대 담기지 않는다 — 이후 `SensitiveDiagnosticsFilter`가
     * key 이름 기준으로 한 번 더 걸러낸다(방어적 이중 조치).
     *
     * @return array<string, string>
     */
    public function collectExportSnapshot(): array
    {
        $diagnostics = $this->collect();

        return [
            'app_version' => $this->appVersion,
            'app_env' => $diagnostics['environment']['APP_ENV'],
            'php_version' => PHP_VERSION,
            'php_sapi' => PHP_SAPI,
            'php_extensions' => implode(',', get_loaded_extensions()),
            'db_status' => $diagnostics['db']['status'],
            'db_driver_version' => $diagnostics['db']['version'],
            'schema_status' => $diagnostics['schema']['status'],
            'schema_migration' => $diagnostics['schema']['migration'],
            'cache_status' => $diagnostics['cache']['status'],
            'cache_usage' => $diagnostics['cache']['usage'],
            'generated_at' => (new \DateTimeImmutable('now'))->format(DATE_ATOM),
        ];
    }

    /**
     * @return array{status: string, version: string}
     */
    private function collectDatabase(): array
    {
        if ($this->pdo === null) {
            return [
                'status' => $this->dbConnectionStatus === 'error' ? '오류' : '미설정',
                'version' => '-',
            ];
        }

        try {
            $driver = (string) $this->pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
            $serverVersion = (string) $this->pdo->getAttribute(PDO::ATTR_SERVER_VERSION);
        } catch (\Throwable) {
            return ['status' => '오류', 'version' => '-'];
        }

        return [
            'status' => '연결됨',
            'version' => trim($driver . ' ' . $serverVersion),
        ];
    }

    /**
     * @return array{status: string, migration: string}
     */
    private function collectSchema(): array
    {
        if ($this->pdo === null) {
            return ['status' => '확인 불가', 'migration' => '-'];
        }

        try {
            $statement = $this->pdo->query('SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1');
            $row = $statement !== false ? $statement->fetch(PDO::FETCH_ASSOC) : false;
        } catch (\Throwable) {
            return ['status' => '미적용', 'migration' => '스키마 없음'];
        }

        if ($row === false || !isset($row['version'])) {
            return ['status' => '미적용', 'migration' => '버전 기록 없음'];
        }

        return ['status' => '적용됨', 'migration' => (string) $row['version']];
    }

    /**
     * @return array{status: string, usage: string}
     */
    private function collectCache(): array
    {
        $redisUrl = $this->configLoader->get('redis_url');
        if (is_string($redisUrl) && trim($redisUrl) !== '') {
            return $this->collectRedisCache($redisUrl);
        }

        return $this->collectFileCache();
    }

    /**
     * @return array{status: string, usage: string}
     */
    private function collectFileCache(): array
    {
        $path = $this->storagePathConfig->cachePath();
        $reachable = is_dir($path) && is_writable($path);

        return [
            'status' => $reachable ? '사용 가능' : '접근 불가',
            'usage' => 'file:' . $path,
        ];
    }

    /**
     * @return array{status: string, usage: string}
     */
    private function collectRedisCache(string $redisUrl): array
    {
        if (!class_exists(\Redis::class)) {
            return ['status' => '접근 불가', 'usage' => 'redis(확장 미설치)'];
        }

        $parts = parse_url($redisUrl);
        if ($parts === false || !isset($parts['host'])) {
            return ['status' => '접근 불가', 'usage' => 'redis(설정 오류)'];
        }

        $reachable = false;
        try {
            $redis = new \Redis();
            $reachable = $redis->connect($parts['host'], $parts['port'] ?? 6379, 0.5);
            $redis->close();
        } catch (\Throwable) {
            $reachable = false;
        }

        return [
            'status' => $reachable ? '사용 가능' : '접근 불가',
            'usage' => 'redis:' . $parts['host'],
        ];
    }

    /**
     * @return array<string, string>
     */
    private function collectEnvironment(): array
    {
        $appEnv = $this->configLoader->get('environment', 'production');

        return [
            'APP_VERSION' => $this->appVersion,
            'PHP_VERSION' => PHP_VERSION,
            'PHP_SAPI' => PHP_SAPI,
            'APP_ENV' => is_string($appEnv) ? $appEnv : 'production',
        ];
    }
}
