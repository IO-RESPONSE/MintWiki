"""일반 감사 이벤트 도메인 모델."""
from datetime import datetime
from typing import Optional


class AuditEvent:
    """
    감사 이벤트를 나타내는 도메인 모델.

    감사 이벤트는 ACL/Discussion/Document 등 다양한 모듈의 변경 내역을
    통합 저장하는 append-only 기록이다. 이벤트를 생성한 뒤 내용이
    변경되지 않으므로 생성 이후 수정/삭제 불가능하다.
    """

    def __init__(
        self,
        id: str,
        category: str,
        action: str,
        entity_id: str,
        occurred_at: datetime,
        related_entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        """
        감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자 (uuid4)
            category: 이벤트의 카테고리 ("acl", "discussion" 등)
            action: 이벤트의 액션 (enum 값을 문자열로)
            entity_id: 변경 대상의 주요 id (rule_id, thread_id 등)
            occurred_at: 변경이 발생한 시각
            related_entity_id: 부가 참조 id (document_id, comment_id 등)
            actor_id: 변경을 수행한 사용자의 id (선택사항)
        """
        self.id = id
        self.category = category
        self.action = action
        self.entity_id = entity_id
        self.related_entity_id = related_entity_id
        self.actor_id = actor_id
        self.occurred_at = occurred_at
