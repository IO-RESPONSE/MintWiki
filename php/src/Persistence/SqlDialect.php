<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

/**
 * 지원하는 SQL 방언을 나타내는 열거형 (태스크 0486).
 *
 * `ConnectionConfig`가 저장하는 driver 문자열(pgsql, mysql, sqlite)을
 * 타입 안전하게 다루기 위해 사용한다. `PdoConnectionFactory`와
 * `PdoTransaction` 위에 실제 SQL 실행 로직이 추가될 때, 방언별 처리가
 * 필요한 부분에서 이 enum으로 동작을 분기한다.
 */
enum SqlDialect: string
{
    case MySQL = 'mysql';
    case PostgreSQL = 'pgsql';
    case SQLite = 'sqlite';

    /**
     * 문자열 driver 값으로부터 enum 사례를 얻는다. 지원하지 않는 driver는
     * null을 반환한다.
     */
    public static function tryFromDriver(string $driver): ?self
    {
        return self::tryFrom($driver);
    }

    /**
     * 문자열 driver 값으로부터 enum 사례를 얻는다. 지원하지 않는 driver에
     * 대해 InvalidArgumentException을 던진다.
     */
    public static function fromDriver(string $driver): self
    {
        return self::tryFromDriver($driver)
            ?? throw new \InvalidArgumentException(
                sprintf('지원하지 않는 SQL 방언입니다: %s', $driver)
            );
    }
}
