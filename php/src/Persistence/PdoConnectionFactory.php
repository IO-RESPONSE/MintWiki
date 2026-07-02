<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

use InvalidArgumentException;
use PDO;

/**
 * `ConnectionConfig`로부터 PDO DSN 문자열을 조립하고 `PDO` 인스턴스를 만드는
 * 골격 (태스크 0484).
 *
 * `docs/db-adapter-contract.md` §1(연결/세션 소유권)에 따라, 이 factory는
 * 애플리케이션 조립 계층에서만 호출된다 — 만들어진 `PDO` 인스턴스는
 * Repository 생성자에 주입되며, Repository/Service는 이 클래스를 직접
 * 알지 못한다. 트랜잭션 wrapper(0485)와 SQL dialect enum(0486)은 이후
 * 태스크에서 이 위에 추가된다.
 */
final class PdoConnectionFactory
{
    /** MariaDB(mysql) 연결의 기본 문자셋. `docs/mariadb-compatibility-matrix.md`에 따라 3바이트 utf8이 아니라 utf8mb4를 반드시 쓴다. */
    private const MARIADB_CHARSET = 'utf8mb4';

    /**
     * `docs/postgresql-dsn-compatibility.md`가 정리한 필드(host, port,
     * database)를 driver별 PDO DSN 문자열로 조립한다. 지원 driver는
     * `pgsql`(PostgreSQL)과 `mysql`(MariaDB) 두 가지뿐이다.
     */
    public static function dsn(ConnectionConfig $config): string
    {
        return match ($config->driver()) {
            'pgsql' => sprintf(
                'pgsql:host=%s;port=%d;dbname=%s',
                $config->host(),
                $config->port(),
                $config->database()
            ),
            'mysql' => sprintf(
                'mysql:host=%s;port=%d;dbname=%s;charset=%s',
                $config->host(),
                $config->port(),
                $config->database(),
                self::MARIADB_CHARSET
            ),
            default => throw new InvalidArgumentException(
                sprintf('지원하지 않는 PDO driver입니다: %s', $config->driver())
            ),
        };
    }

    /**
     * `dsn()`이 조립한 DSN으로 실제 `PDO` 연결을 연다. 예외는 항상 던지도록
     * `PDO::ERRMODE_EXCEPTION`을 강제한다(`docs/db-adapter-contract.md`
     * §3의 통합 제약 위반 신호 전달 전제).
     */
    public static function connect(ConnectionConfig $config): PDO
    {
        return new PDO(
            self::dsn($config),
            $config->username(),
            $config->password(),
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
    }
}
