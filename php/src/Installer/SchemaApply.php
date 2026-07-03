<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use RuntimeException;

/**
 * 설치 스키마 적용 placeholder.
 *
 * 실제 SQL 적용은 이후 태스크에서 연결하고, 지금은 dry-run/confirm 흐름만 보장한다.
 */
final class SchemaApply
{
    /**
     * 스키마 적용 요청을 처리한다.
     *
     * @param bool $dryRun true이면 적용 없이 계획만 반환한다.
     * @param bool $confirmed 실제 적용 모드에서 사용자가 확인했는지 여부.
     *
     * @return array{mode:string,confirmed:bool,applied:bool,message:string}
     *
     * @throws RuntimeException 실제 적용 모드에서 확인이 없을 때.
     */
    public function apply(bool $dryRun, bool $confirmed = false): array
    {
        if ($dryRun) {
            return [
                'mode' => 'dry-run',
                'confirmed' => false,
                'applied' => false,
                'message' => '스키마 적용 dry-run입니다. 데이터베이스는 변경하지 않습니다.',
            ];
        }

        if (!$confirmed) {
            throw new RuntimeException('스키마 적용에는 확인이 필요합니다.');
        }

        return [
            'mode' => 'confirm',
            'confirmed' => true,
            'applied' => false,
            'message' => '스키마 적용 placeholder입니다. 아직 실제 SQL은 실행하지 않습니다.',
        ];
    }
}
