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
 * 스키마 파일은 배포 시 docroot(`php/public`) 밖 `db/` 형제 디렉터리에 위치하므로,
 * 기본 경로는 이 파일 기준(`php/src/Installer`) 상위로 3단계 거슬러 올라간
 * 저장소 루트에 `db/schema`를 붙여 계산한다. 테스트에서는 실제 DB 없이 검증할 수
 * 있도록 fixture 디렉터리를 생성자 인자로 주입할 수 있게 했다.
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
        return $this->schemaDir ?? dirname(__DIR__, 3) . '/db/schema';
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
