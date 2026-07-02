"""관리자 활동 보고서 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import List, Optional

from modules.admin.report import AdminReport


class DuplicateAdminReportIdError(Exception):
    """보고서 id가 중복될 때 발생하는 예외."""

    pass


class AdminReportRepository(ABC):
    """
    관리자 활동 보고서 저장소의 인터페이스.

    저장소는 보고서를 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, report: AdminReport) -> AdminReport:
        """
        새로운 관리자 활동 보고서를 저장소에 저장한다.

        Args:
            report: 저장할 관리자 활동 보고서

        Returns:
            저장된 관리자 활동 보고서

        Raises:
            DuplicateAdminReportIdError: 동일한 id의 보고서가 이미 존재하는 경우
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[AdminReport]:
        """
        주어진 id로 관리자 활동 보고서를 조회한다.

        Args:
            id: 조회할 보고서의 고유 식별자

        Returns:
            조회된 보고서 또는 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_actor_id(self, actor_id: str) -> List[AdminReport]:
        """
        주어진 관리자 id로 보고서들을 조회한다.

        Args:
            actor_id: 조회할 관리자의 고유 식별자

        Returns:
            조회된 보고서의 리스트 (없으면 빈 리스트)
        """
        pass

    @abstractmethod
    async def list_all(self) -> List[AdminReport]:
        """
        저장소에 저장된 모든 관리자 활동 보고서를 조회한다.

        Returns:
            모든 보고서의 리스트 (없으면 빈 리스트)
        """
        pass


class InMemoryAdminReportRepository(AdminReportRepository):
    """
    메모리에 관리자 활동 보고서를 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.reports: dict[str, AdminReport] = {}
        self.actor_id_index: dict[str, list[str]] = {}

    async def create(self, report: AdminReport) -> AdminReport:
        """
        새로운 관리자 활동 보고서를 저장소에 저장한다.

        보고서 저장소는 append-only이므로 동일한 id의 보고서가 이미 존재하면
        DuplicateAdminReportIdError를 발생시킨다.

        Args:
            report: 저장할 관리자 활동 보고서

        Returns:
            저장된 관리자 활동 보고서

        Raises:
            DuplicateAdminReportIdError: 동일한 id의 보고서가 이미 존재하는 경우
        """
        if report.id in self.reports:
            raise DuplicateAdminReportIdError(
                f"id '{report.id}'인 보고서가 이미 존재합니다"
            )

        self.reports[report.id] = report

        if report.actor_id:
            if report.actor_id not in self.actor_id_index:
                self.actor_id_index[report.actor_id] = []
            self.actor_id_index[report.actor_id].append(report.id)

        return report

    async def get(self, id: str) -> Optional[AdminReport]:
        """
        주어진 id로 관리자 활동 보고서를 조회한다.

        Args:
            id: 조회할 보고서의 고유 식별자

        Returns:
            조회된 보고서 또는 없으면 None
        """
        return self.reports.get(id)

    async def get_by_actor_id(self, actor_id: str) -> List[AdminReport]:
        """
        주어진 관리자 id로 보고서들을 조회한다.

        Args:
            actor_id: 조회할 관리자의 고유 식별자

        Returns:
            조회된 보고서의 리스트 (없으면 빈 리스트)
        """
        report_ids = self.actor_id_index.get(actor_id, [])
        return [self.reports[report_id] for report_id in report_ids]

    async def list_all(self) -> List[AdminReport]:
        """
        저장소에 저장된 모든 관리자 활동 보고서를 조회한다.

        Returns:
            모든 보고서의 리스트 (없으면 빈 리스트)
        """
        return list(self.reports.values())
