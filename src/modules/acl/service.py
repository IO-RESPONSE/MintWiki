"""ACL 권한 검사 서비스."""
from typing import List, Optional

from modules.acl.decision import Decision
from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Rule, SubjectType


class AclService:
    """
    문서에 대한 권한 검사를 담당하는 서비스.

    문서별 ACL 규칙(DocumentAcl)이 있으면 우선 적용하고, 없으면
    네임스페이스 기본 규칙(NamespaceAclDefaults)으로 대체한다. 규칙은
    등록된 순서대로 검사하여 대상과 권한이 일치하는 첫 번째 규칙의
    effect를 결과로 사용한다.

    규칙 우선순위(allow/deny 충돌 처리)나 그룹 소속 검사 같은 세부
    평가 로직은 이후 태스크에서 채워진다. 이 서비스는 일치하는 규칙이
    없을 때 안전하게 거부하는 기본 동작만 제공하는 골격이다.
    """

    def __init__(self, namespace_defaults: Optional[NamespaceAclDefaults] = None):
        """
        서비스를 초기화한다.

        Args:
            namespace_defaults: 네임스페이스 기본 규칙 저장소 (선택사항)
        """
        self.namespace_defaults = namespace_defaults

    def check(
        self,
        permission: Permission,
        subject_type: SubjectType,
        subject_id: Optional[str] = None,
        document_acl: Optional[DocumentAcl] = None,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> Decision:
        """
        주어진 대상이 문서에 대해 특정 권한을 가지는지 검사한다.

        Args:
            permission: 검사할 권한 종류
            subject_type: 검사 대상의 종류 (사용자, 그룹, 익명, 전체)
            subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)
            document_acl: 문서에 등록된 ACL (선택사항, 없으면 네임스페이스
                기본 규칙을 사용)
            namespace: 문서가 속한 네임스페이스 (기본값 DEFAULT_NAMESPACE)

        Returns:
            검사 결과를 담은 Decision. 일치하는 규칙이 없으면 거부(deny)로 판단한다.
        """
        for rule in self._resolve_rules(document_acl, namespace):
            if rule.permission is not permission:
                continue
            if not rule.applies_to(subject_type, subject_id):
                continue
            return Decision(
                permission=permission,
                allowed=rule.is_allow(),
                reason=f"matched rule {rule.id}",
                matched_rule_id=rule.id,
            )

        return Decision(
            permission=permission,
            allowed=False,
            reason="no matching rule",
        )

    def _resolve_rules(
        self, document_acl: Optional[DocumentAcl], namespace: str
    ) -> List[Rule]:
        """검사에 사용할 규칙 목록을 결정한다."""
        if document_acl is not None and document_acl.has_rules():
            return document_acl.rules()
        if self.namespace_defaults is not None:
            return self.namespace_defaults.get(namespace)
        return []
