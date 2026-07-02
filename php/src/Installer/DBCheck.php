<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use PDO;
use RuntimeException;

/**
 * 설치 프로세스에서 데이터베이스 상태를 검사하는 클래스.
 *
 * 데이터베이스 연결 가능 여부, 문자셋 설정, 스키마 버전을 확인한다.
 */
final class DBCheck
{
    /**
     * 초기화.
     */
    public function __construct()
    {
    }

    /**
     * 데이터베이스 연결을 테스트한다.
     *
     * PDO 인스턴스에서 간단한 쿼리를 실행하여 연결 가능 여부를 확인한다.
     *
     * @param PDO $connection 테스트할 PDO 연결.
     *
     * @return bool 연결이 가능하면 true.
     *
     * @throws RuntimeException 연결 실패 시.
     */
    public function isConnectionValid(PDO $connection): bool
    {
        try {
            $connection->query('SELECT 1');
            return true;
        } catch (\Exception $e) {
            throw new RuntimeException('데이터베이스 연결이 유효하지 않습니다: ' . $e->getMessage());
        }
    }

    /**
     * 데이터베이스 문자셋이 올바른지 확인한다.
     *
     * MariaDB는 utf8mb4, PostgreSQL은 UTF8을 확인한다.
     *
     * @param PDO $connection 테스트할 PDO 연결.
     * @param string $driver 데이터베이스 드라이버 (mysql, pgsql).
     *
     * @return bool 문자셋이 올바르면 true.
     *
     * @throws RuntimeException 문자셋 확인 실패 시.
     */
    public function isCharsetValid(PDO $connection, string $driver): bool
    {
        try {
            if ($driver === 'mysql') {
                return $this->isMariadbCharsetValid($connection);
            } elseif ($driver === 'pgsql') {
                return $this->isPostgresqlCharsetValid($connection);
            } else {
                throw new RuntimeException("지원하지 않는 드라이버: {$driver}");
            }
        } catch (\Exception $e) {
            throw new RuntimeException('문자셋 확인 실패: ' . $e->getMessage());
        }
    }

    /**
     * MariaDB/MySQL 문자셋이 utf8mb4인지 확인한다.
     *
     * @param PDO $connection 테스트할 PDO 연결.
     *
     * @return bool utf8mb4이면 true.
     */
    private function isMariadbCharsetValid(PDO $connection): bool
    {
        $result = $connection->query('SELECT @@character_set_client AS charset')->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return false;
        }

        $charset = $result['charset'] ?? null;
        return $charset === 'utf8mb4';
    }

    /**
     * PostgreSQL 문자셋이 UTF8인지 확인한다.
     *
     * @param PDO $connection 테스트할 PDO 연결.
     *
     * @return bool UTF8이면 true.
     */
    private function isPostgresqlCharsetValid(PDO $connection): bool
    {
        $result = $connection->query("SHOW client_encoding")->fetch(PDO::FETCH_ASSOC);
        if (!$result) {
            return false;
        }

        $encoding = $result['client_encoding'] ?? null;
        return $encoding === 'UTF8';
    }

    /**
     * 스키마 버전 테이블이 존재하고 데이터가 있는지 확인한다.
     *
     * @param PDO $connection 테스트할 PDO 연결.
     *
     * @return bool 스키마 버전이 적용되어 있으면 true.
     *
     * @throws RuntimeException 스키마 확인 실패 시.
     */
    public function isSchemaVersionValid(PDO $connection): bool
    {
        try {
            $result = $connection->query(
                'SELECT COUNT(*) as count FROM schema_version'
            )->fetch(PDO::FETCH_ASSOC);

            if (!$result) {
                return false;
            }

            $count = (int) ($result['count'] ?? 0);
            return $count > 0;
        } catch (\Exception $e) {
            throw new RuntimeException('스키마 버전 확인 실패: ' . $e->getMessage());
        }
    }
}
