"""
마이그레이션 상태 조회 서비스.

배포된 스키마 버전 및 마이그레이션 적용 상태를 DB 엔진 독립적으로
조회하는 서비스.
"""

from typing import Optional
from datetime import datetime


class MigrationStateService:
    """마이그레이션 상태를 조회하는 서비스."""

    def __init__(self):
        """초기화."""
        pass

    def get_current_version(
        self, versions: list
    ) -> Optional[tuple[str, datetime]]:
        """
        현재 적용된 스키마 버전을 반환한다.

        Args:
            versions: SchemaVersionORM 인스턴스 리스트.

        Returns:
            (버전 문자열, applied_at) 튜플. 버전이 없으면 None.
        """
        if not versions:
            return None

        # 최신 applied_at 기준으로 정렬하여 가장 최근 버전 반환
        sorted_versions = sorted(
            versions, key=lambda v: v.applied_at, reverse=True
        )
        latest = sorted_versions[0]
        return (latest.version, latest.applied_at)

    def get_applied_versions(self, versions: list) -> list[str]:
        """
        적용된 모든 버전을 버전 순서대로 반환한다.

        Args:
            versions: SchemaVersionORM 인스턴스 리스트.

        Returns:
            버전 문자열 리스트.
        """
        version_strings = [v.version for v in versions]
        return sorted(version_strings)

    def is_version_applied(self, versions: list, version: str) -> bool:
        """
        특정 버전이 이미 적용되었는지 확인한다.

        Args:
            versions: SchemaVersionORM 인스턴스 리스트.
            version: 확인할 버전 문자열.

        Returns:
            버전이 적용되었으면 True, 아니면 False.
        """
        return any(v.version == version for v in versions)

    def get_version_count(self, versions: list) -> int:
        """
        적용된 버전의 개수를 반환한다.

        Args:
            versions: SchemaVersionORM 인스턴스 리스트.

        Returns:
            적용된 버전의 개수.
        """
        return len(versions)
