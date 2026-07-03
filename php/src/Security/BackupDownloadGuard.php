<?php

declare(strict_types=1);

namespace MintWiki\Security;

use RuntimeException;

/**
 * 백업 다운로드 요청의 최소 보안 경계를 제공한다.
 *
 * 실제 파일 전송은 후속 작업에서 담당하고, 여기서는 관리자 권한과 경로 순회
 * 차단을 먼저 통과한 백업 파일 경로만 반환한다.
 */
final class BackupDownloadGuard
{
    public const REQUIRED_PERMISSION = 'admin:read';

    public function __construct(
        private readonly PathTraversalGuard $pathGuard = new PathTraversalGuard()
    ) {
    }

    /**
     * 관리자 권한과 안전한 상대 경로를 확인한 뒤 다운로드 대상 경로를 반환한다.
     *
     * @param list<string> $permissions 현재 사용자의 권한 목록
     *
     * @throws RuntimeException 관리자 권한이 없는 경우
     */
    public function guardedPath(string $backupBasePath, string $requestedPath, array $permissions): string
    {
        if (!in_array(self::REQUIRED_PERMISSION, $permissions, true)) {
            throw new RuntimeException('백업 다운로드에는 관리자 권한이 필요합니다.');
        }

        return $this->pathGuard->join($backupBasePath, $requestedPath);
    }
}
