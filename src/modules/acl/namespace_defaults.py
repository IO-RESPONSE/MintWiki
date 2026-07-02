"""네임스페이스별 기본 ACL 규칙 정의."""
from typing import Dict, List

from modules.acl.rule import Rule

DEFAULT_NAMESPACE = "*"


class NamespaceAclDefaults:
    """
    네임스페이스별 기본 ACL 규칙 집합을 관리한다.

    문서에 별도의 ACL 규칙이 없을 때 네임스페이스 단위로 적용할 기본
    규칙을 등록하고 조회한다. 특정 네임스페이스에 등록된 규칙이 없으면
    DEFAULT_NAMESPACE로 등록된 규칙을 대신 반환한다.
    """

    def __init__(self):
        self._rules_by_namespace: Dict[str, List[Rule]] = {}

    def register(self, namespace: str, rules: List[Rule]) -> None:
        """주어진 네임스페이스에 대한 기본 규칙 목록을 등록한다."""
        self._rules_by_namespace[namespace] = list(rules)

    def get(self, namespace: str) -> List[Rule]:
        """
        네임스페이스에 등록된 기본 규칙을 반환한다.

        해당 네임스페이스에 등록된 규칙이 없으면 DEFAULT_NAMESPACE에
        등록된 규칙을 반환하고, 그마저도 없으면 빈 목록을 반환한다.
        """
        if namespace in self._rules_by_namespace:
            return list(self._rules_by_namespace[namespace])
        return list(self._rules_by_namespace.get(DEFAULT_NAMESPACE, []))
