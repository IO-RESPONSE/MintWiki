"""관리자 활동 보고서 저장소 인터페이스 테스트."""
from datetime import datetime

import pytest

from modules.admin.report import AdminReport
from modules.admin.report_repository import (
    AdminReportRepository,
    DuplicateAdminReportIdError,
    InMemoryAdminReportRepository,
)


class TestAdminReportRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            AdminReportRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(AdminReportRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(AdminReportRepository, "get")

    def test_get_by_actor_id_method_exists(self):
        """저장소는 get_by_actor_id 메서드를 정의한다."""
        assert hasattr(AdminReportRepository, "get_by_actor_id")

    def test_list_all_method_exists(self):
        """저장소는 list_all 메서드를 정의한다."""
        assert hasattr(AdminReportRepository, "list_all")


class TestInMemoryAdminReportRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_report(self):
        """인메모리 저장소는 보고서를 생성할 수 있다."""
        repo = InMemoryAdminReportRepository()
        report = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
        )
        result = await repo.create(report)
        assert result.id == "report-1"
        assert result.generated_at == datetime(2026, 1, 1)

    @pytest.mark.asyncio
    async def test_can_fetch_report_by_id(self):
        """인메모리 저장소는 id로 보고서를 조회할 수 있다."""
        repo = InMemoryAdminReportRepository()
        report = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        await repo.create(report)
        result = await repo.get("report-1")
        assert result is not None
        assert result.id == "report-1"
        assert result.actor_id == "admin-1"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryAdminReportRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_fetch_reports_by_actor_id(self):
        """인메모리 저장소는 관리자 id로 보고서들을 조회할 수 있다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        report2 = AdminReport(
            id="report-2",
            generated_at=datetime(2026, 1, 2),
            actor_id="admin-1",
        )
        report3 = AdminReport(
            id="report-3",
            generated_at=datetime(2026, 1, 3),
            actor_id="admin-2",
        )
        await repo.create(report1)
        await repo.create(report2)
        await repo.create(report3)

        results = await repo.get_by_actor_id("admin-1")
        assert len(results) == 2
        assert results[0].id == "report-1"
        assert results[1].id == "report-2"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_missing_actor_id(self):
        """인메모리 저장소는 없는 관리자 id를 조회하면 빈 리스트를 반환한다."""
        repo = InMemoryAdminReportRepository()
        result = await repo.get_by_actor_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_list_all_reports(self):
        """인메모리 저장소는 모든 보고서를 조회할 수 있다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        report2 = AdminReport(
            id="report-2",
            generated_at=datetime(2026, 1, 2),
            actor_id="admin-2",
        )
        await repo.create(report1)
        await repo.create(report2)

        results = await repo.list_all()
        assert len(results) == 2
        assert results[0].id == "report-1"
        assert results[1].id == "report-2"

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_list_for_empty_repo(self):
        """인메모리 저장소는 비어있으면 list_all에서 빈 리스트를 반환한다."""
        repo = InMemoryAdminReportRepository()
        result = await repo.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_can_store_multiple_reports_with_different_actors(self):
        """인메모리 저장소는 여러 관리자의 보고서를 저장할 수 있다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        report2 = AdminReport(
            id="report-2",
            generated_at=datetime(2026, 1, 2),
            actor_id="admin-2",
        )
        report3 = AdminReport(
            id="report-3",
            generated_at=datetime(2026, 1, 3),
            actor_id="admin-3",
        )
        await repo.create(report1)
        await repo.create(report2)
        await repo.create(report3)

        all_reports = await repo.list_all()
        admin1_reports = await repo.get_by_actor_id("admin-1")
        admin2_reports = await repo.get_by_actor_id("admin-2")
        admin3_reports = await repo.get_by_actor_id("admin-3")

        assert len(all_reports) == 3
        assert len(admin1_reports) == 1
        assert len(admin2_reports) == 1
        assert len(admin3_reports) == 1

    @pytest.mark.asyncio
    async def test_preserves_report_details_through_create_and_get(self):
        """인메모리 저장소는 조회 시 보고서 세부사항을 유지한다."""
        repo = InMemoryAdminReportRepository()
        generated_at = datetime(2026, 1, 1, 12, 30, 45)
        start_at = datetime(2026, 1, 1)
        end_at = datetime(2026, 1, 31)
        report = AdminReport(
            id="report-1",
            generated_at=generated_at,
            actor_id="admin-1",
            start_at=start_at,
            end_at=end_at,
        )
        await repo.create(report)

        result = await repo.get("report-1")
        assert result.id == "report-1"
        assert result.generated_at == generated_at
        assert result.actor_id == "admin-1"
        assert result.start_at == start_at
        assert result.end_at == end_at

    @pytest.mark.asyncio
    async def test_raises_on_duplicate_report_id(self):
        """인메모리 저장소는 동일한 id로 생성 시 DuplicateAdminReportIdError를 발생시킨다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        report2 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 2),
            actor_id="admin-2",
        )
        await repo.create(report1)
        with pytest.raises(DuplicateAdminReportIdError):
            await repo.create(report2)

    @pytest.mark.asyncio
    async def test_report_ordering_in_get_by_actor_id(self):
        """인메모리 저장소는 관리자별 조회 시 생성 순서를 유지한다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id="admin-1",
        )
        report2 = AdminReport(
            id="report-2",
            generated_at=datetime(2026, 1, 2),
            actor_id="admin-1",
        )
        report3 = AdminReport(
            id="report-3",
            generated_at=datetime(2026, 1, 3),
            actor_id="admin-1",
        )
        await repo.create(report1)
        await repo.create(report2)
        await repo.create(report3)

        results = await repo.get_by_actor_id("admin-1")
        assert [r.id for r in results] == ["report-1", "report-2", "report-3"]

    @pytest.mark.asyncio
    async def test_report_without_actor_id_not_indexed(self):
        """인메모리 저장소는 관리자 id가 없는 보고서를 actor_id 인덱스에 저장하지 않는다."""
        repo = InMemoryAdminReportRepository()
        report = AdminReport(
            id="report-1",
            generated_at=datetime(2026, 1, 1),
            actor_id=None,
        )
        await repo.create(report)

        results = await repo.get_by_actor_id("admin-1")
        assert results == []

        all_reports = await repo.list_all()
        assert len(all_reports) == 1
        assert all_reports[0].id == "report-1"

    @pytest.mark.asyncio
    async def test_duplicate_error_message_includes_id(self):
        """중복 id 에러 메시지가 해당 id를 포함한다."""
        repo = InMemoryAdminReportRepository()
        report1 = AdminReport(
            id="duplicate-report-123",
            generated_at=datetime(2026, 1, 1),
        )
        report2 = AdminReport(
            id="duplicate-report-123",
            generated_at=datetime(2026, 1, 2),
        )
        await repo.create(report1)

        with pytest.raises(DuplicateAdminReportIdError) as exc_info:
            await repo.create(report2)

        assert "duplicate-report-123" in str(exc_info.value)
