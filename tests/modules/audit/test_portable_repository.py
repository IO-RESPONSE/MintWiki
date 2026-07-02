"""감사 이벤트 저장소 portability 테스트.

docs/portable-id-column-policy.md, docs/portable-query-builder-policy.md,
docs/audit-portable-repository-plan.md 가 정한 정책을 `DatabaseAuditRepository`가
실제로 만족하는지 검증한다. 이 테스트의 초점은 감사 이벤트가 append-only
경계를 지키면서 ID 컬럼과 쿼리 빌더 정책을 만족하는지 확인하는 것이다.
"""
import re
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.audit.audit_event import AuditEvent
from modules.audit.repository import DatabaseAuditRepository
from persistence.base import Base

UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.fixture
async def async_db_session():
    """테스트용 인메모리 SQLite 데이터베이스 세션을 생성한다."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestPortableIdColumnPolicy:
    """docs/portable-id-column-policy.md: id는 애플리케이션이 uuid4 문자열로 생성한다."""

    @pytest.mark.asyncio
    async def test_stores_and_returns_uuid4_id_unchanged(self, async_db_session):
        """소문자 uuid4 하이픈 문자열 id가 가공 없이 그대로 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        assert UUID4_PATTERN.match(event_id)

        event = AuditEvent(
            id=event_id,
            category="acl",
            action="rule_added",
            entity_id="rule1",
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.id == event_id
        assert UUID4_PATTERN.match(result.id)

    @pytest.mark.asyncio
    async def test_does_not_rely_on_db_generated_id(self, async_db_session):
        """DB의 자동 증가/시퀀스 없이 애플리케이션이 지정한 id가 그대로 유지된다."""
        repo = DatabaseAuditRepository(async_db_session)
        first_id = str(uuid.uuid4())
        second_id = str(uuid.uuid4())

        await repo.append(
            AuditEvent(
                id=first_id,
                category="acl",
                action="rule_added",
                entity_id="rule1",
                occurred_at=datetime.now(timezone.utc),
            )
        )
        await repo.append(
            AuditEvent(
                id=second_id,
                category="acl",
                action="rule_removed",
                entity_id="rule2",
                occurred_at=datetime.now(timezone.utc),
            )
        )

        # id는 생성 순서가 아니라 애플리케이션이 지정한 값으로 조회된다.
        assert (await repo.get(first_id)).id == first_id
        assert (await repo.get(second_id)).id == second_id

    @pytest.mark.asyncio
    async def test_entity_id_and_related_entity_id_round_trip_unchanged(
        self, async_db_session
    ):
        """entity_id와 related_entity_id FK 컬럼도 uuid4 문자열 형식을 가공 없이 저장/조회한다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        related_entity_id = str(uuid.uuid4())

        event = AuditEvent(
            id=event_id,
            category="acl",
            action="rule_added",
            entity_id=entity_id,
            related_entity_id=related_entity_id,
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.entity_id == entity_id
        assert result.related_entity_id == related_entity_id


class TestPortableQueryBuilderPolicy:
    """docs/portable-query-builder-policy.md: 값은 항상 바인드 파라미터로 전달된다.

    쿼리 빌더 대신 문자열을 이어 붙여 SQL을 조립했다면, 아래처럼 SQL 문법에서
    의미를 갖는 문자(따옴표, 세미콜론, SQL 키워드)가 포함된 값이 저장/조회
    과정에서 깨지거나 예외를 일으켰을 것이다.
    """

    @pytest.mark.asyncio
    async def test_action_with_sql_metacharacters_round_trips_unchanged(
        self, async_db_session
    ):
        """SQL 인젝션 시도처럼 보이는 action 값도 그대로 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        malicious_action = "rule_added'; DROP TABLE audit_event; --"

        event = AuditEvent(
            id=event_id,
            category="acl",
            action=malicious_action,
            entity_id="rule1",
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.action == malicious_action

    @pytest.mark.asyncio
    async def test_entity_id_with_quotes_round_trips_unchanged(
        self, async_db_session
    ):
        """작은따옴표가 포함된 entity_id가 손상 없이 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        entity_id = "rule's-id-123"

        event = AuditEvent(
            id=event_id,
            category="acl",
            action="rule_added",
            entity_id=entity_id,
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.entity_id == entity_id

    @pytest.mark.asyncio
    async def test_category_with_sql_keywords_round_trips_unchanged(
        self, async_db_session
    ):
        """SQL 키워드를 포함한 category 값도 손상 없이 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        # 실제로는 고정 카테고리지만, 테스트를 위해 SQL 키워드를 포함한 문자열 사용
        category = "SELECT * FROM audit_event"

        event = AuditEvent(
            id=event_id,
            category=category,
            action="test_action",
            entity_id="entity1",
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.category == category

    @pytest.mark.asyncio
    async def test_actor_id_with_quotes_round_trips_unchanged(
        self, async_db_session
    ):
        """작은따옴표가 포함된 actor_id가 손상 없이 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        actor_id = "user's-id"

        event = AuditEvent(
            id=event_id,
            category="acl",
            action="rule_added",
            entity_id="rule1",
            actor_id=actor_id,
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.actor_id == actor_id

    @pytest.mark.asyncio
    async def test_table_survives_metacharacter_insert_attempt(
        self, async_db_session
    ):
        """메타문자가 포함된 값을 저장해도 다른 감사 이벤트 데이터가 온전히 유지된다."""
        repo = DatabaseAuditRepository(async_db_session)
        first_event_id = str(uuid.uuid4())
        second_event_id = str(uuid.uuid4())

        # 안전한 이벤트 먼저 추가
        await repo.append(
            AuditEvent(
                id=first_event_id,
                category="acl",
                action="safe_action",
                entity_id="safe_rule",
                occurred_at=datetime.now(timezone.utc),
            )
        )

        # 메타문자가 포함된 이벤트 추가
        await repo.append(
            AuditEvent(
                id=second_event_id,
                category="acl",
                action="Malicious'; DROP TABLE audit_event; --",
                entity_id="rule1",
                occurred_at=datetime.now(timezone.utc),
            )
        )

        # 첫 번째 이벤트가 그대로 남는다.
        survivor = await repo.get(first_event_id)
        assert survivor is not None
        assert survivor.action == "safe_action"
        assert survivor.entity_id == "safe_rule"

    @pytest.mark.asyncio
    async def test_mixed_quotes_in_multiple_fields_round_trip_unchanged(
        self, async_db_session
    ):
        """여러 필드에 걸쳐 다양한 따옴표가 있는 값도 정확히 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())

        event = AuditEvent(
            id=event_id,
            category="discussion",
            action='comment_added; "quoted" action',
            entity_id="thread's-id",
            related_entity_id='comment-"id"',
            actor_id="user's-name",
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.action == 'comment_added; "quoted" action'
        assert result.entity_id == "thread's-id"
        assert result.related_entity_id == 'comment-"id"'
        assert result.actor_id == "user's-name"


class TestAuditAppendOnlyPortability:
    """docs/audit-portable-repository-plan.md: append-only 경계를 둔다.

    감사 이벤트는 생성 이후 수정하거나 삭제할 수 없으며, 오직 추가(append)만
    가능해야 한다. 저장소 인터페이스에는 append 메서드만 있고 update/delete는
    없다.
    """

    @pytest.mark.asyncio
    async def test_repository_only_has_append_method(self, async_db_session):
        """저장소는 append 메서드만 제공하고 update/delete는 없다."""
        repo = DatabaseAuditRepository(async_db_session)

        # append 메서드는 존재한다.
        assert hasattr(repo, "append")
        assert callable(repo.append)

        # update/delete 메서드는 없다.
        assert not hasattr(repo, "update")
        assert not hasattr(repo, "delete")

    @pytest.mark.asyncio
    async def test_append_adds_event_in_order(self, async_db_session):
        """여러 이벤트를 순서대로 추가할 수 있다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_ids = []

        for i in range(5):
            event_id = str(uuid.uuid4())
            event = AuditEvent(
                id=event_id,
                category="acl",
                action=f"action_{i}",
                entity_id=f"rule_{i}",
                occurred_at=datetime.now(timezone.utc),
            )
            await repo.append(event)
            event_ids.append(event_id)

        # 모든 이벤트가 추가되었다.
        for event_id in event_ids:
            result = await repo.get(event_id)
            assert result is not None

    @pytest.mark.asyncio
    async def test_append_and_list_maintains_order(self, async_db_session):
        """카테고리별 이벤트 조회가 추가 순서를 유지한다."""
        repo = DatabaseAuditRepository(async_db_session)
        category = "acl"

        event_ids = []
        for i in range(3):
            event_id = f"event_{i:02d}"
            await repo.append(
                AuditEvent(
                    id=event_id,
                    category=category,
                    action=f"action_{i}",
                    entity_id=f"rule_{i}",
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            event_ids.append(event_id)

        # 카테고리별 조회 시 추가 순서가 유지된다 (id 타이브레이커로 일관성 보장).
        result = await repo.list_by_category(category)
        result_ids = [e.id for e in result]
        assert result_ids == sorted(event_ids)

    @pytest.mark.asyncio
    async def test_append_with_optional_fields(self, async_db_session):
        """선택사항 필드(related_entity_id, actor_id)가 None일 수 있다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())

        # related_entity_id와 actor_id 없이 추가
        event = AuditEvent(
            id=event_id,
            category="acl",
            action="rule_added",
            entity_id="rule1",
            occurred_at=datetime.now(timezone.utc),
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        assert result.related_entity_id is None
        assert result.actor_id is None

    @pytest.mark.asyncio
    async def test_append_preserves_occurred_at_timestamp(self, async_db_session):
        """occurred_at 타임스탬프가 정확히 저장/조회된다."""
        repo = DatabaseAuditRepository(async_db_session)
        event_id = str(uuid.uuid4())
        occurred_at = datetime(2026, 7, 2, 12, 30, 45, tzinfo=timezone.utc)

        event = AuditEvent(
            id=event_id,
            category="discussion",
            action="thread_created",
            entity_id="thread1",
            occurred_at=occurred_at,
        )
        await repo.append(event)
        result = await repo.get(event_id)

        assert result is not None
        # 타임스탬프를 초 단위로 비교 (마이크로초는 DB에 따라 다를 수 있음)
        # SQLite는 timezone 정보를 제거할 수 있으므로, naive 형식으로 비교
        result_no_tz = result.occurred_at.replace(microsecond=0, tzinfo=None)
        expected_no_tz = occurred_at.replace(microsecond=0, tzinfo=None)
        assert result_no_tz == expected_no_tz

    @pytest.mark.asyncio
    async def test_list_by_entity_id_returns_related_events(self, async_db_session):
        """엔티티 id별로 조회 시 관련 이벤트들이 모두 반환된다."""
        repo = DatabaseAuditRepository(async_db_session)
        entity_id = "rule_123"
        event_ids = []

        for i in range(3):
            event_id = str(uuid.uuid4())
            await repo.append(
                AuditEvent(
                    id=event_id,
                    category="acl",
                    action=f"action_{i}",
                    entity_id=entity_id,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            event_ids.append(event_id)

        result = await repo.list_by_entity_id(entity_id)
        result_ids = {e.id for e in result}
        assert result_ids == set(event_ids)

    @pytest.mark.asyncio
    async def test_empty_queries_return_empty_lists(self, async_db_session):
        """존재하지 않는 카테고리/엔티티 조회는 빈 목록을 반환한다."""
        repo = DatabaseAuditRepository(async_db_session)

        # 빈 카테고리 조회
        result = await repo.list_by_category("nonexistent_category")
        assert result == []

        # 빈 엔티티 조회
        result = await repo.list_by_entity_id("nonexistent_entity")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, async_db_session):
        """존재하지 않는 id 조회는 None을 반환한다."""
        repo = DatabaseAuditRepository(async_db_session)
        result = await repo.get(str(uuid.uuid4()))
        assert result is None
