<?php

declare(strict_types=1);

namespace MintWiki\App;

use MintWiki\Persistence\ConnectionConfig;
use MintWiki\Persistence\PdoConnectionFactory;
use PDO;

/**
 * 애플리케이션 부트스트랩 진입점 (태스크 0673).
 *
 * `LocalConfigLoader` → `ConnectionConfig` → `PdoConnectionFactory` 순서로
 * 설정을 읽어 PDO 연결을 만든다. `index.php` 등 프론트 컨트롤러 연결은
 * 0674에서 수행하며, 이 클래스는 그 전 단계인 "설정으로부터 PDO를 얻는"
 * 조립 로직만 담당한다.
 *
 * DB 설정이 없는 환경(로컬 개발, 배포 직후 미설치 상태)에서도 예외 없이
 * 동작해야 하므로, 설정 파싱(`connectionConfig()`)과 실제 접속 시도
 * (`pdo()`)를 분리했다 — 파싱 단계는 네트워크 의존 없이 단위 테스트가
 * 가능하고, 접속 단계는 생성자로 주입 가능한 connector를 통해 테스트에서
 * 대체할 수 있다.
 *
 * @see LocalConfigLoader
 * @see \MintWiki\Persistence\ConnectionConfig
 * @see \MintWiki\Persistence\PdoConnectionFactory
 */
final class AppBootstrap
{
    private const DEFAULT_PORTS = [
        'mysql' => 3306,
        'pgsql' => 5432,
    ];

    /** @var callable(ConnectionConfig): PDO */
    private $connector;

    /**
     * @param string|null $configDir 설정 파일(`config/.env`,
     *     `config/local-config.php`)이 위치한 디렉터리. null이면
     *     `LocalConfigLoader`의 기본 경로(`php/config`)를 사용한다.
     *     테스트에서 fixture 디렉터리를 주입할 때 이 인자를 사용한다.
     * @param (callable(ConnectionConfig): PDO)|null $connector 실제 PDO
     *     연결을 여는 함수. null이면 `PdoConnectionFactory::connect()`를
     *     사용한다. 테스트에서는 실제 DB 서버 없이 동작을 검증하기 위해
     *     가짜 connector를 주입할 수 있다.
     */
    public function __construct(
        private readonly ?string $configDir = null,
        ?callable $connector = null
    ) {
        $this->connector = $connector ?? static fn (ConnectionConfig $config): PDO
            => PdoConnectionFactory::connect($config);
    }

    /**
     * 설정 파일들을 읽어 `ConnectionConfig`를 구성한다. 실제 접속은
     * 시도하지 않는다 — DB 설정이 하나도 없으면 예외 대신 null을 반환한다.
     */
    public function connectionConfig(): ?ConnectionConfig
    {
        $localConfigLoader = new LocalConfigLoader($this->configDir);
        $configLoader = new ConfigLoader($localConfigLoader->load());

        $dsn = $configLoader->get('mariadb_dsn');
        if (is_string($dsn) && trim($dsn) !== '') {
            return $this->fromMariadbDsn($dsn, $configLoader);
        }

        $databaseUrl = $configLoader->get('database_url');
        if (is_string($databaseUrl) && trim($databaseUrl) !== '') {
            return $this->fromDatabaseUrl($databaseUrl);
        }

        return null;
    }

    /**
     * `connectionConfig()`로 얻은 설정으로 실제 PDO 연결을 만든다. DB
     * 설정이 없으면 예외를 던지지 않고 null을 반환한다("미설정" 상태).
     */
    public function pdo(): ?PDO
    {
        $config = $this->connectionConfig();
        if ($config === null) {
            return null;
        }

        return ($this->connector)($config);
    }

    /**
     * PDO DSN 형식(`mysql:host=...;port=...;dbname=...`)의 `mariadb_dsn`
     * 값을 `ConnectionConfig`로 변환한다. 사용자명/비밀번호는
     * `local-config.php`가 채워주는 `mariadb_user`/`mariadb_password`에서
     * 가져온다(둘 다 PDO DSN 문자열 자체에는 포함되지 않는다).
     */
    private function fromMariadbDsn(string $dsn, ConfigLoader $configLoader): ?ConnectionConfig
    {
        if (!str_contains($dsn, ':')) {
            return null;
        }

        [$driver, $paramString] = explode(':', $dsn, 2);

        $params = [];
        foreach (explode(';', $paramString) as $pair) {
            if (!str_contains($pair, '=')) {
                continue;
            }
            [$key, $value] = explode('=', $pair, 2);
            $params[trim($key)] = trim($value);
        }

        if (!isset($params['host'], $params['dbname'])) {
            return null;
        }

        $defaultPort = self::DEFAULT_PORTS[$driver] ?? 0;
        $port = isset($params['port']) ? (int) $params['port'] : $defaultPort;

        $username = $configLoader->get('mariadb_user', '');
        $password = $configLoader->get('mariadb_password', '');

        return new ConnectionConfig(
            $driver,
            $params['host'],
            $port,
            $params['dbname'],
            is_string($username) ? $username : '',
            is_string($password) ? $password : ''
        );
    }

    /**
     * `scheme://user:pass@host:port/dbname` 형식의 `database_url` 값을
     * `ConnectionConfig`로 변환한다.
     */
    private function fromDatabaseUrl(string $databaseUrl): ?ConnectionConfig
    {
        $parts = parse_url($databaseUrl);
        if ($parts === false || !isset($parts['scheme'], $parts['host'], $parts['path'])) {
            return null;
        }

        $driver = match ($parts['scheme']) {
            'mysql' => 'mysql',
            'postgresql', 'postgres' => 'pgsql',
            default => $parts['scheme'],
        };

        $port = $parts['port'] ?? self::DEFAULT_PORTS[$driver] ?? 0;
        $database = ltrim($parts['path'], '/');

        if ($database === '') {
            return null;
        }

        return new ConnectionConfig(
            $driver,
            $parts['host'],
            $port,
            $database,
            $parts['user'] ?? '',
            $parts['pass'] ?? ''
        );
    }
}
