"""관리자 활동 보고서 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.admin.report import (
    AdminReport,
    EmptyAdminReportIdError,
)


class TestAdminReportCreation:
    """보고서 생성 테스트."""

    def test_creates_report_with_required_fields(self):
        """필수 필드로 보고서를 생성할 수 있다."""
        report = AdminReport(
            id="report1",
            generated_at=datetime(2026, 1, 1),
        )

        assert report.id == "report1"
        assert report.generated_at == datetime(2026, 1, 1)
        assert report.actor_id is None
        assert report.start_at is None
        assert report.end_at is None

    def test_creates_report_with_all_fields(self):
        """모든 필드로 보고서를 생성할 수 있다."""
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)
        generated = datetime(2026, 2, 1)

        report = AdminReport(
            id="report1",
            generated_at=generated,
            actor_id="admin1",
            start_at=start,
            end_at=end,
        )

        assert report.id == "report1"
        assert report.generated_at == generated
        assert report.actor_id == "admin1"
        assert report.start_at == start
        assert report.end_at == end

    def test_raises_error_when_id_is_empty(self):
        """id가 비어있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminReportIdError):
            AdminReport(
                id="",
                generated_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_id_is_whitespace(self):
        """id가 공백만 있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminReportIdError):
            AdminReport(
                id="   ",
                generated_at=datetime(2026, 1, 1),
            )
