"""문서별 ACL 규칙 도메인 모델."""
from typing import List, Optional

from modules.acl.rule import Rule


class EmptyDocumentIdError(Exception):
    """문서 id가 비어있을 때 발생."""

    pass


class DocumentAcl:
    """
    특정 문서에 직접 적용되는 ACL 규칙 집합을 나타내는 도메인 모델.

    네임스페이스 기본 규칙(NamespaceAclDefaults)과 달리, 이 모델은 하나의
    문서 id에 결부된 규칙 목록만을 관리한다. 규칙이 없을 때 네임스페이스
    기본값으로 대체할지 여부는 상위 서비스가 판단한다.
    """

    def __init__(self, document_id: str, rules: Optional[List[Rule]] = None):
        """
        문서 ACL을 생성한다.

        Args:
            document_id: 규칙이 적용되는 문서의 고유 식별자
            rules: 문서에 등록할 규칙 목록 (선택사항, 기본값 빈 목록)

        Raises:
            EmptyDocumentIdError: 문서 id가 비어있거나 공백만 있는 경우
        """
        if not document_id or not document_id.strip():
            raise EmptyDocumentIdError("문서 id는 비어있을 수 없습니다")

        self.document_id = document_id
        self._rules: List[Rule] = list(rules) if rules else []

    def add_rule(self, rule: Rule) -> None:
        """문서에 규칙을 추가한다."""
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        """문서에서 주어진 id의 규칙을 제거한다. 없으면 아무 동작도 하지 않는다."""
        self._rules = [rule for rule in self._rules if rule.id != rule_id]

    def rules(self) -> List[Rule]:
        """문서에 등록된 규칙 목록을 반환한다."""
        return list(self._rules)

    def has_rules(self) -> bool:
        """문서에 등록된 규칙이 하나라도 있는지 확인한다."""
        return len(self._rules) > 0
