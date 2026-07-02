"""마이그레이션 상태 서비스 테스트."""

from datetime import datetime
import pytest

from persistence.migration_state_service import MigrationStateService
from persistence.models import SchemaVersionORM


class MockSchemaVersion:
    """SchemaVersionORM을 모방한 테스트용 클래스."""

    def __init__(self, version: str, applied_at: datetime):
        """
        초기화.

        Args:
            version: 버전 문자열.
            applied_at: 적용 시간.
        """
        self.version = version
        self.applied_at = applied_at


class TestMigrationStateService:
    """MigrationStateService 테스트."""

    def setup_method(self):
        """테스트 전 설정."""
        self.service = MigrationStateService()

    def test_service_initialization(self):
        """서비스를 초기화할 수 있는지 확인한다."""
        assert self.service is not None

    def test_get_current_version_with_empty_list(self):
        """버전 목록이 비어있을 때 None을 반환한다."""
        result = self.service.get_current_version([])
        assert result is None

    def test_get_current_version_with_single_version(self):
        """단일 버전이 있을 때 현재 버전을 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        version = MockSchemaVersion("v1.0.0", now)

        result = self.service.get_current_version([version])

        assert result is not None
        assert result[0] == "v1.0.0"
        assert result[1] == now

    def test_get_current_version_with_multiple_versions(self):
        """여러 버전이 있을 때 가장 최신 버전을 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        early = datetime.fromisoformat("2026-07-01T18:00:00+00:00")
        latest = datetime.fromisoformat("2026-07-02T19:00:00+00:00")

        versions = [
            MockSchemaVersion("v1.0.0", early),
            MockSchemaVersion("v1.1.0", now),
            MockSchemaVersion("v1.2.0", latest),
        ]

        result = self.service.get_current_version(versions)

        assert result is not None
        assert result[0] == "v1.2.0"
        assert result[1] == latest

    def test_get_applied_versions_with_empty_list(self):
        """버전 목록이 비어있을 때 빈 리스트를 반환한다."""
        result = self.service.get_applied_versions([])
        assert result == []

    def test_get_applied_versions_returns_sorted_versions(self):
        """적용된 모든 버전을 정렬하여 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")

        versions = [
            MockSchemaVersion("v1.2.0", now),
            MockSchemaVersion("v1.0.0", now),
            MockSchemaVersion("v1.1.0", now),
        ]

        result = self.service.get_applied_versions(versions)

        assert result == ["v1.0.0", "v1.1.0", "v1.2.0"]

    def test_is_version_applied_returns_true_when_version_exists(self):
        """버전이 적용되어 있으면 True를 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        versions = [
            MockSchemaVersion("v1.0.0", now),
            MockSchemaVersion("v1.1.0", now),
        ]

        assert self.service.is_version_applied(versions, "v1.0.0")
        assert self.service.is_version_applied(versions, "v1.1.0")

    def test_is_version_applied_returns_false_when_version_not_exists(self):
        """버전이 적용되어 있지 않으면 False를 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        versions = [
            MockSchemaVersion("v1.0.0", now),
            MockSchemaVersion("v1.1.0", now),
        ]

        assert not self.service.is_version_applied(versions, "v1.2.0")
        assert not self.service.is_version_applied(versions, "v2.0.0")

    def test_is_version_applied_with_empty_list(self):
        """빈 버전 목록에서 항상 False를 반환한다."""
        assert not self.service.is_version_applied([], "v1.0.0")

    def test_get_version_count_with_empty_list(self):
        """버전 목록이 비어있을 때 0을 반환한다."""
        result = self.service.get_version_count([])
        assert result == 0

    def test_get_version_count_with_multiple_versions(self):
        """적용된 버전의 개수를 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        versions = [
            MockSchemaVersion("v1.0.0", now),
            MockSchemaVersion("v1.1.0", now),
            MockSchemaVersion("v1.2.0", now),
        ]

        result = self.service.get_version_count(versions)

        assert result == 3

    def test_get_version_count_with_single_version(self):
        """단일 버전의 개수를 반환한다."""
        now = datetime.fromisoformat("2026-07-02T18:00:00+00:00")
        versions = [MockSchemaVersion("v1.0.0", now)]

        result = self.service.get_version_count(versions)

        assert result == 1
