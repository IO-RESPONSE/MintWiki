<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

/**
 * PDO 연결 하나를 만드는 데 필요한 설정을 표현하는 불변 value object (태스크 0484).
 *
 * `docs/postgresql-dsn-compatibility.md`가 정리한 필드 단위 비교(user,
 * password, host, port, database 이름)를 그대로 따른다 — driver 값으로
 * `pgsql`(PostgreSQL)과 `mysql`(MariaDB)만 표현하고, 실제 DSN 문자열
 * 조립은 `PdoConnectionFactory`가 담당한다.
 */
final class ConnectionConfig
{
    public function __construct(
        private readonly string $driver,
        private readonly string $host,
        private readonly int $port,
        private readonly string $database,
        private readonly string $username,
        private readonly string $password
    ) {
    }

    public function driver(): string
    {
        return $this->driver;
    }

    public function host(): string
    {
        return $this->host;
    }

    public function port(): int
    {
        return $this->port;
    }

    public function database(): string
    {
        return $this->database;
    }

    public function username(): string
    {
        return $this->username;
    }

    public function password(): string
    {
        return $this->password;
    }
}
