<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use MintWiki\Persistence\ConnectionConfig;
use MintWiki\Persistence\PdoConnectionFactory;
use PDO;
use RuntimeException;

/**
 * 설치 마법사가 입력받은 DB 접속 정보를 `local-config.php`로 기록하는 클래스 (태스크 0679).
 *
 * `LocalConfigLoader`/`AppBootstrap`(0673)이 읽는 것과 동일한 경로
 * (`config/local-config.php`)와 배열 구조(`config/database.php.sample`)로 기록해,
 * 설치 후 앱이 부트스트랩 단계에서 그대로 읽을 수 있게 한다. 접속 시험
 * (`testConnection()`)과 기록(`write()`)을 분리해, 접속 실패 시에는 아무것도
 * 기록하지 않는 흐름을 호출자가 조합할 수 있게 한다.
 *
 * 접속 시험에 실제 네트워크를 타지 않아도 되도록, `PdoConnectionFactory::connect()`
 * 호출을 connector로 주입 가능하게 했다(`AppBootstrap`과 동일한 패턴) — 테스트에서
 * 성공/실패를 가짜 connector로 재현할 수 있다.
 */
final class DatabaseConfigWriter
{
    private const CONFIG_FILENAME = 'local-config.php';

    /** @var callable(ConnectionConfig): PDO */
    private $connector;

    /**
     * @param string|null $configDir local-config.php를 기록할 디렉터리. null이면
     *     `LocalConfigLoader`의 기본 경로(`php/config`)를 사용한다.
     * @param (callable(ConnectionConfig): PDO)|null $connector 실제 PDO 연결을
     *     여는 함수. null이면 `PdoConnectionFactory::connect()`를 사용한다.
     */
    public function __construct(
        private readonly ?string $configDir = null,
        ?callable $connector = null
    ) {
        $this->connector = $connector ?? static fn (ConnectionConfig $config): PDO
            => PdoConnectionFactory::connect($config);
    }

    /**
     * 기록 대상 파일의 전체 경로를 반환한다.
     */
    public function path(): string
    {
        $configDir = $this->configDir ?? dirname(__DIR__, 2) . '/config';

        return $configDir . '/' . self::CONFIG_FILENAME;
    }

    /**
     * 주어진 접속 정보로 실제 접속을 시험한다. 실패하면 connector가 던지는
     * 예외를 그대로 전파한다 — 호출자는 이 예외를 잡아 폼 오류로 변환한다.
     */
    public function testConnection(ConnectionConfig $config): void
    {
        ($this->connector)($config);
    }

    /**
     * 접속 정보를 `database.php.sample` 구조로 `local-config.php`에 기록한다.
     * 파일 권한을 0600으로 제한해 비밀번호가 다른 사용자에게 노출되지 않게 한다.
     */
    public function write(ConnectionConfig $config): void
    {
        $configDir = $this->configDir ?? dirname(__DIR__, 2) . '/config';

        if (!is_dir($configDir)) {
            throw new RuntimeException('설정 디렉터리가 없습니다: ' . $configDir);
        }

        if (!is_writable($configDir)) {
            throw new RuntimeException('설정 디렉터리에 쓸 수 없습니다: ' . $configDir);
        }

        $path = $this->path();
        $content = $this->buildFileContents($config);

        if (file_put_contents($path, $content, LOCK_EX) === false) {
            throw new RuntimeException('설정 파일을 기록할 수 없습니다: ' . $path);
        }

        if (!chmod($path, 0600)) {
            throw new RuntimeException('설정 파일 권한을 제한할 수 없습니다: ' . $path);
        }
    }

    /**
     * `database.php.sample`과 동일한 배열 구조의 PHP 소스를 만든다.
     */
    private function buildFileContents(ConnectionConfig $config): string
    {
        $dsn = PdoConnectionFactory::dsn($config);

        return "<?php\n\n"
            . "declare(strict_types=1);\n\n"
            . "// 설치 마법사(태스크 0679)가 기록한 데이터베이스 설정. config/database.php.sample 참고.\n"
            . "return [\n"
            . "    'driver' => " . var_export($config->driver(), true) . ",\n"
            . "    'dsn' => " . var_export($dsn, true) . ",\n"
            . "    'user' => " . var_export($config->username(), true) . ",\n"
            . "    'password' => " . var_export($config->password(), true) . ",\n"
            . "    'options' => [\n"
            . "        \\PDO::ATTR_ERRMODE => \\PDO::ERRMODE_EXCEPTION,\n"
            . "        \\PDO::ATTR_DEFAULT_FETCH_MODE => \\PDO::FETCH_ASSOC,\n"
            . "    ],\n"
            . "];\n";
    }
}
