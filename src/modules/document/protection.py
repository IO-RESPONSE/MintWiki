"""문서 보호 도메인 모델."""
from datetime import datetime
from typing import Optional


class Protection:
    """
    문서 보호를 나타내는 도메인 모델.

    보호는 문서에 대한 수정 권한을 제한한다. 보호는 고유한 id, 보호될
    문서의 id, 생성 시각, 선택적으로 만료 시각과 보호 사유, 그리고 보호를
    설정한 관리자의 id를 가진다.
    """

    def __init__(
        self,
        id: str,
        document_id: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None,
        protected_by: Optional[str] = None,
    ):
        """
        문서 보호를 생성한다.

        Args:
            id: 보호의 고유 식별자
            document_id: 보호할 문서의 id
            created_at: 보호가 생성된 시각
            expires_at: 보호 만료 시각 (선택사항, None이면 무기한)
            reason: 보호 사유 (선택사항)
            protected_by: 보호를 설정한 관리자의 id (선택사항)
        """
        self.id = id
        self.document_id = document_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.reason = reason
        self.protected_by = protected_by

    def is_active(self, now: datetime) -> bool:
        """
        주어진 시각을 기준으로 보호가 활성 상태인지 확인한다.

        Args:
            now: 확인 기준이 되는 시각

        Returns:
            보호가 유효하면 True, 만료되었으면 False
        """
        if self.expires_at is None:
            return True
        return now < self.expires_at
