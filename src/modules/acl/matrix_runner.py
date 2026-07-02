"""ACL 권한 매트릭스 픽스처 실행 러너."""
from typing import List, NamedTuple, Optional

from modules.acl.matrix_fixture import AclMatrixCase, AclMatrixFixture
from modules.acl.service import AclService


class AclMatrixCaseResult(NamedTuple):
    """매트릭스 케이스 하나를 AclService로 실행한 결과."""

    fixture_name: str
    case: AclMatrixCase
    actual_allowed: bool
    actual_matched_rule_id: Optional[str]

    def passed(self) -> bool:
        """실제 판단 결과가 케이스의 기대값과 일치하는지 확인한다."""
        if self.actual_allowed != self.case.expected_allowed:
            return False
        if self.case.expected_matched_rule_id is None:
            return True
        return self.actual_matched_rule_id == self.case.expected_matched_rule_id

    def describe(self) -> str:
        """실패 원인을 사람이 읽을 수 있는 문자열로 설명한다."""
        return (
            f"{self.fixture_name}: {self.case.subject_type}/{self.case.subject_id} "
            f"{self.case.permission} expected allowed={self.case.expected_allowed} "
            f"(rule={self.case.expected_matched_rule_id}), actual allowed="
            f"{self.actual_allowed} (rule={self.actual_matched_rule_id})"
        )


class AclMatrixRunner:
    """ACL 매트릭스 픽스처의 케이스들을 AclService에 대해 실행하는 러너."""

    def __init__(self, service: Optional[AclService] = None):
        """
        러너를 초기화한다.

        Args:
            service: 케이스 판단에 사용할 AclService. 기본값은 새 인스턴스.
        """
        self.service = service if service is not None else AclService()

    def run_fixture(self, fixture: AclMatrixFixture) -> List[AclMatrixCaseResult]:
        """
        하나의 매트릭스 픽스처에 속한 모든 케이스를 실행한다.

        Args:
            fixture: 실행할 ACL 매트릭스 픽스처

        Returns:
            픽스처의 각 케이스에 대한 실행 결과 목록
        """
        document_acl = fixture.document_acl()
        results = []
        for case in fixture.cases:
            decision = self.service.check(
                permission=case.permission,
                subject_type=case.subject_type,
                subject_id=case.subject_id,
                document_acl=document_acl,
            )
            results.append(
                AclMatrixCaseResult(
                    fixture_name=fixture.name,
                    case=case,
                    actual_allowed=decision.is_allowed(),
                    actual_matched_rule_id=decision.matched_rule_id,
                )
            )
        return results

    def run_all(self, fixtures: List[AclMatrixFixture]) -> List[AclMatrixCaseResult]:
        """
        여러 매트릭스 픽스처를 순서대로 실행한다.

        Args:
            fixtures: 실행할 ACL 매트릭스 픽스처 목록

        Returns:
            모든 픽스처의 모든 케이스에 대한 실행 결과 목록
        """
        results: List[AclMatrixCaseResult] = []
        for fixture in fixtures:
            results.extend(self.run_fixture(fixture))
        return results

    def failures(self, fixtures: List[AclMatrixFixture]) -> List[AclMatrixCaseResult]:
        """
        여러 매트릭스 픽스처를 실행하고 기대값과 어긋난 결과만 반환한다.

        Args:
            fixtures: 실행할 ACL 매트릭스 픽스처 목록

        Returns:
            기대값과 일치하지 않는 실행 결과 목록
        """
        return [result for result in self.run_all(fixtures) if not result.passed()]


__all__ = ["AclMatrixCaseResult", "AclMatrixRunner"]
