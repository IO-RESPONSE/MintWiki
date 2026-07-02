"""ACL 권한 검사 결과 도메인 모델."""
from typing import Optional

from modules.acl.permission import Permission


class Decision:
    """
    하나의 권한 검사 요청에 대한 결과를 나타내는 도메인 모델.

    허용 여부(allowed)와 검사한 권한(permission)뿐 아니라, 그 결과가 나온
    근거(reason)와 근거가 된 규칙 id(matched_rule_id)를 함께 담아 상위
    호출자가 왜 이런 결과가 나왔는지 추적할 수 있게 한다. 여러 규칙을
    조합해 이 결과를 산출하는 로직은 이 모델이 아닌 ACL 서비스가 담당한다.
    """

    def __init__(
        self,
        permission: Permission,
        allowed: bool,
        reason: str,
        matched_rule_id: Optional[str] = None,
    ):
        """
        권한 검사 결과를 생성한다.

        Args:
            permission: 검사한 권한 종류
            allowed: 권한이 허용되었는지 여부
            reason: 이 결과가 나온 근거를 설명하는 문자열
            matched_rule_id: 결과의 근거가 된 규칙의 id (선택사항)
        """
        self.permission = permission
        self.allowed = allowed
        self.reason = reason
        self.matched_rule_id = matched_rule_id

    def is_allowed(self) -> bool:
        """검사 결과가 허용인지 확인한다."""
        return self.allowed

    def is_denied(self) -> bool:
        """검사 결과가 거부인지 확인한다."""
        return not self.allowed
