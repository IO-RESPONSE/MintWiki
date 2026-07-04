<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use PDO;
use RuntimeException;
use Throwable;

/**
 * 설치 마법사가 `db/schema/*.sql`을 FK 의존 순서로 적용하는 클래스.
 *
 * 태스크 0623에서는 dry-run/confirm 흐름만 있는 placeholder였고, 이 태스크(0680)에서
 * 실제 SQL 적용을 연결한다. FK 순서는 `scripts/mariadb_smoke_check.py`의
 * `SCHEMA_ORDER`와 동일하다 — 두 목록이 어긋나면 smoke test와 installer가 서로
 * 다른 순서로 테이블을 만들게 된다.
 *
 * 스키마 파일은 배포 시 docroot(`php/public`) 밖에 위치하는데, 그 정확한 층은
 * 배포 레이아웃마다 다르다:
 *   - 저장소/SSH 릴리스: `<root>/php/src`와 `<root>/db/schema` (src 기준 3단계 위)
 *   - iowiki 평탄 FTP: docroot 형제로 `src/`와 `db/`가 같은 층 (src 기준 2단계 위)
 * 고정 깊이(`dirname(__DIR__, 3)`)로는 두 레이아웃을 동시에 맞출 수 없으므로,
 * 기본 경로는 이 파일 기준 상위 디렉터리를 거슬러 올라가며 스키마 SQL이 실제
 * 존재하는 위치(`.../db/schema` 또는 `.../db`)를 탐색해 계산한다. 테스트에서는
 * 실제 DB 없이 검증할 수 있도록 fixture 디렉터리를 생성자 인자로 주입할 수 있게 했다.
 */
final class SchemaApply
{
    private const SCHEMA_ORDER = [
        'schema_migration.sql',
        'schema_version.sql',
        'account.sql',
        'document.sql',
        'revision.sql',
        'user_session.sql',
        'acl_rule.sql',
        'acl_namespace_rule.sql',
        'discussion_thread.sql',
        'discussion_comment.sql',
        'audit_event.sql',
        'job.sql',
    ];

    public function __construct(private readonly ?string $schemaDir = null)
    {
    }

    /**
     * 스키마 SQL 파일이 위치한 디렉터리 경로.
     */
    public function schemaDir(): string
    {
        if ($this->schemaDir !== null) {
            return $this->schemaDir;
        }

        // 이 파일 기준 상위 디렉터리를 거슬러 올라가며 스키마 SQL이 실제 존재하는
        // 위치를 찾는다. `db/schema`(저장소/릴리스 레이아웃)를 `db`(평탄 FTP
        // 레이아웃, docroot 형제)보다 먼저 확인해 저장소 기준 경로를 우선한다.
        $marker = self::SCHEMA_ORDER[0];
        $dir = __DIR__;
        $previous = '';
        while ($dir !== $previous) {
            foreach (['/db/schema', '/db'] as $suffix) {
                $candidate = $dir . $suffix;
                if (is_file($candidate . '/' . $marker)) {
                    return $candidate;
                }
            }

            $previous = $dir;
            $dir = dirname($dir);
        }

        // 어느 레이아웃에서도 찾지 못하면 저장소 기준 기본값을 반환해, 호출부가
        // `apply()`에서 명확한 "스키마 파일을 찾을 수 없습니다" 오류를 내게 한다.
        return dirname(__DIR__, 3) . '/db/schema';
    }

    /**
     * `db/schema`의 SQL 파일을 FK 의존 순서로 적용하고, 전부 성공하면
     * `schema_version`에 버전 행을 기록한다.
     *
     * DDL은 MariaDB/PostgreSQL 모두 트랜잭션으로 되돌릴 수 없으므로, 중간에
     * 실패한 파일 이전까지 이미 적용된 테이블은 그대로 남는다 — 호출자는 예외를
     * 잡아 설치 화면에 오류로 보여주고 다음 단계로 넘어가지 않으면 된다.
     *
     * @return string[] 적용에 성공한 파일 이름 목록(순서대로).
     *
     * @throws RuntimeException 스키마 파일을 찾을 수 없거나 SQL 실행이 실패했을 때.
     */
    public function apply(PDO $pdo, string $version): array
    {
        $schemaDir = $this->schemaDir();
        $applied = [];

        $this->prepareConnection($pdo);

        foreach (self::SCHEMA_ORDER as $filename) {
            $path = $schemaDir . '/' . $filename;

            if (!is_file($path)) {
                throw new RuntimeException("스키마 파일을 찾을 수 없습니다: {$path}");
            }

            $sql = file_get_contents($path);
            if ($sql === false) {
                throw new RuntimeException("스키마 파일을 읽을 수 없습니다: {$path}");
            }

            try {
                $pdo->exec($sql);
            } catch (Throwable $exception) {
                throw new RuntimeException("스키마 적용 실패 ({$filename}): " . $exception->getMessage(), 0, $exception);
            }

            $applied[] = $filename;
        }

        $this->recordSchemaVersion($pdo, $version);

        return $applied;
    }

    /**
     * 스키마 적용 전에 연결을 준비한다. MariaDB(mysql 드라이버)는 기본 스토리지
     * 엔진이 MyISAM(인덱스 키 최대 1000바이트)인 공유 호스팅이 있는데,
     * discussion_thread의 복합 인덱스(document_id, created_at, id)처럼 VARCHAR
     * 여러 개를 묶은 인덱스가 이 한도를 넘어 1071 오류로 실패한다. 스키마 파일은
     * PostgreSQL 이식성 때문에 `ENGINE=`을 명시하지 않으므로, 여기서 세션 기본
     * 엔진을 InnoDB(DYNAMIC 행 포맷, 키 최대 3072바이트)로 지정해 해결한다.
     * SQLite 등 다른 드라이버에서는 이 구문이 없으므로 건너뛴다.
     */
    private function prepareConnection(PDO $pdo): void
    {
        if ($pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql') {
            $pdo->exec('SET SESSION default_storage_engine=InnoDB');
        }
    }

    /**
     * 적용이 모두 끝난 뒤 `schema_version` 테이블에 버전 행을 기록한다.
     * `InstallerRouteGate`/`DBCheck`가 설치 완료 여부를 이 테이블의 행 존재로
     * 판단하므로, 이 호출이 끝나야 비로소 설치가 완료된 것으로 취급된다.
     */
    private function recordSchemaVersion(PDO $pdo, string $version): void
    {
        $statement = $pdo->prepare(
            'INSERT INTO schema_version (version, applied_at) VALUES (:version, :applied_at)'
        );
        $statement->execute([
            'version' => $version,
            'applied_at' => gmdate('Y-m-d H:i:s'),
        ]);
    }
}
