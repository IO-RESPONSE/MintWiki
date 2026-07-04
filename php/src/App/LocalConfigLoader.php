<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 로컬 설정 파일 로더 (태스크 0616).
 *
 * php/config 디렉토리의 설정 파일들을 읽어서 ConfigLoader에 전달할
 * 값 배열을 구성한다. 환경변수가 없어도 파일 설정으로부터 값을 읽을 수
 * 있다.
 *
 * 지원하는 파일:
 * - .env 파일: key=value 형식의 환경변수
 * - local-config.php: PHP 배열 반환 파일 (database.php.sample 기반)
 *
 * 조회 우선순위: .env → local-config.php → 기본값
 *
 * @see ConfigLoader
 */
final class LocalConfigLoader
{
    private string $configDir;

    public function __construct(?string $configDir = null)
    {
        if ($configDir === null) {
            // 기본값: php/config 디렉토리
            $configDir = dirname(__DIR__, 2) . '/config';
        }
        $this->configDir = $configDir;
    }

    /**
     * 로컬 설정 파일들을 읽어 ConfigLoader에 전달할 배열을 구성한다.
     *
     * .env 파일이 local-config.php보다 우선한다.
     *
     * @return array<string, mixed> 파일에서 읽은 설정 값들
     */
    public function load(): array
    {
        $values = [];

        // local-config.php 로드 (낮은 우선순위)
        $localConfigFile = $this->configDir . '/local-config.php';
        if (file_exists($localConfigFile)) {
            $fileConfig = $this->loadPhpConfigFile($localConfigFile);
            if (is_array($fileConfig)) {
                $values = array_merge($values, $this->normalizePhpConfig($fileConfig));
            }
        }

        // .env 파일 파싱 (높은 우선순위 — 나중에 로드하므로 덮어씀)
        $envFile = $this->configDir . '/.env';
        if (file_exists($envFile)) {
            $values = array_merge($values, $this->parseEnvFile($envFile));
        }

        return $values;
    }

    /**
     * .env 파일을 파싱하여 key=value 쌍을 추출한다.
     *
     * @param string $filePath 파일 경로
     * @return array<string, string> 파싱된 설정 값들
     */
    private function parseEnvFile(string $filePath): array
    {
        $values = [];

        if (!is_readable($filePath)) {
            return $values;
        }

        $lines = file($filePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($lines === false) {
            return $values;
        }

        foreach ($lines as $line) {
            // 주석 라인 스킵
            if (str_starts_with(trim($line), '#')) {
                continue;
            }

            // = 구분자가 없으면 스킵
            if (!str_contains($line, '=')) {
                continue;
            }

            [$key, $value] = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);

            // 환경변수 접두어 WIKI_ 제거 (ConfigLoader가 추가할 때 사용)
            if (str_starts_with($key, 'WIKI_')) {
                $key = substr($key, 5);
            }

            if ($key !== '') {
                $values[strtolower($key)] = $value;
            }
        }

        return $values;
    }

    /**
     * PHP 설정 파일을 include하고 반환된 배열을 얻는다.
     *
     * @param string $filePath 파일 경로
     * @return mixed include 결과
     */
    private function loadPhpConfigFile(string $filePath): mixed
    {
        if (!is_readable($filePath)) {
            return null;
        }

        // @ 연산자로 파일 읽기 오류 억제 (파일이 없거나 읽을 수 없으면 null 반환)
        return @include($filePath) ?: null;
    }

    /**
     * PHP 설정 파일의 구조를 정규화하여 ConfigLoader 호환 배열로 변환한다.
     *
     * database.php.sample 형식:
     * [
     *     'driver' => 'mysql',
     *     'dsn' => '...',
     *     'user' => '...',
     *     'password' => '...',
     *     'options' => [...]
     * ]
     *
     * @param array<string, mixed> $config PHP 파일에서 반환된 배열
     * @return array<string, mixed> 정규화된 설정 값들 (키는 소문자)
     */
    private function normalizePhpConfig(array $config): array
    {
        $values = [];

        // database.php 구조 변환
        if (isset($config['driver'])) {
            $values['mariadb_driver'] = $config['driver'];
        }
        if (isset($config['dsn'])) {
            $values['mariadb_dsn'] = $config['dsn'];
        }
        if (isset($config['user'])) {
            $values['mariadb_user'] = $config['user'];
        }
        if (isset($config['password'])) {
            $values['mariadb_password'] = $config['password'];
        }

        // 기타 직접 매핑 가능한 키들 (소문자로 통일)
        foreach (['app_name', 'environment', 'database_url', 'redis_url', 'storage_path', 'maintenance_mode'] as $key) {
            if (isset($config[$key])) {
                $values[strtolower($key)] = $config[$key];
            }
        }

        return $values;
    }
}
