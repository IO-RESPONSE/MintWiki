<?php

declare(strict_types=1);

namespace MintWiki\Persistence;

use DateTimeImmutable;

/**
 * 마이그레이션 상태 조회 서비스.
 *
 * 배포된 스키마 버전 및 마이그레이션 적용 상태를 DB 엔진 독립적으로 조회하는 서비스.
 */
final class MigrationStateService
{
    /**
     * 초기화.
     */
    public function __construct()
    {
    }

    /**
     * 현재 적용된 스키마 버전을 반환한다.
     *
     * @param object[] $versions SchemaVersion 행 객체 리스트.
     *                            각 객체는 version (string)과 applied_at (DateTimeImmutable) 속성을 가짐.
     *
     * @return array{0: string, 1: DateTimeImmutable}|null (버전 문자열, applied_at) 튜플. 버전이 없으면 null.
     */
    public function getCurrentVersion(array $versions): ?array
    {
        if (empty($versions)) {
            return null;
        }

        // 최신 applied_at 기준으로 정렬하여 가장 최근 버전 반환
        $sorted = $versions;
        usort($sorted, function (object $a, object $b): int {
            return $b->applied_at <=> $a->applied_at;
        });

        $latest = $sorted[0];
        return [$latest->version, $latest->applied_at];
    }

    /**
     * 적용된 모든 버전을 버전 순서대로 반환한다.
     *
     * @param object[] $versions SchemaVersion 행 객체 리스트.
     *
     * @return string[] 버전 문자열 리스트 (정렬됨).
     */
    public function getAppliedVersions(array $versions): array
    {
        $versionStrings = array_map(static fn (object $v): string => $v->version, $versions);
        sort($versionStrings);
        return $versionStrings;
    }

    /**
     * 특정 버전이 이미 적용되었는지 확인한다.
     *
     * @param object[] $versions SchemaVersion 행 객체 리스트.
     * @param string $version 확인할 버전 문자열.
     *
     * @return bool 버전이 적용되었으면 true, 아니면 false.
     */
    public function isVersionApplied(array $versions, string $version): bool
    {
        foreach ($versions as $v) {
            if ($v->version === $version) {
                return true;
            }
        }
        return false;
    }

    /**
     * 적용된 버전의 개수를 반환한다.
     *
     * @param object[] $versions SchemaVersion 행 객체 리스트.
     *
     * @return int 적용된 버전의 개수.
     */
    public function getVersionCount(array $versions): int
    {
        return count($versions);
    }
}
