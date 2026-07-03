<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use PDO;
use MintWiki\Http\Response;

/**
 * 설치 완료 후 installer 라우트 접근을 차단하는 gate (태스크 0618).
 *
 * 설치 프로세스의 라우트는 설치가 완료되면 더 이상 접근할 수 없어야 한다.
 * 이 gate는 데이터베이스 연결을 통해 설치 상태를 확인하고, 설치 완료 여부에 따라
 * 접근 허용 또는 차단을 결정한다.
 */
final class InstallerRouteGate
{
    private PDO $connection;
    private DBCheck $dbCheck;

    /**
     * 초기화.
     *
     * @param PDO $connection 데이터베이스 연결.
     * @param DBCheck|null $dbCheck DB 검사 인스턴스. 기본값은 새 인스턴스.
     */
    public function __construct(PDO $connection, ?DBCheck $dbCheck = null)
    {
        $this->connection = $connection;
        $this->dbCheck = $dbCheck ?? new DBCheck();
    }

    /**
     * 설치가 이미 완료되었는지 확인한다.
     *
     * schema_version 테이블에 데이터가 1개 이상 있으면 설치가 완료된 것으로 판단한다.
     *
     * @return bool 설치가 완료되었으면 true.
     */
    public function isInstallationComplete(): bool
    {
        try {
            return $this->dbCheck->isSchemaVersionValid($this->connection);
        } catch (\Exception $e) {
            // 스키마 버전 테이블이 없거나 오류가 발생하면 설치가 미완료인 것으로 판단한다.
            return false;
        }
    }

    /**
     * installer 라우트에 접근할 수 있는지 확인한다.
     *
     * 설치가 완료되었으면 false를 반환한다 (접근 불가).
     * 설치가 미완료이면 true를 반환한다 (접근 가능).
     *
     * @return bool 접근 가능하면 true, 차단되면 false.
     */
    public function canAccessInstallerRoute(): bool
    {
        return !$this->isInstallationComplete();
    }

    /**
     * installer 라우트 접근이 차단되었을 때의 응답을 생성한다.
     *
     * 설치가 이미 완료되었으므로 installer 라우트에 접근할 수 없다는 오류를
     * 반환한다. HTTP 403 Forbidden 상태 코드를 사용한다.
     *
     * @return Response installer 라우트 접근 차단 응답.
     */
    public function createBlockedResponse(): Response
    {
        return Response::json([
            'error' => 'installation_already_complete',
            'message' => 'Installation has already been completed. The installer is not available.',
        ], 403);
    }
}
