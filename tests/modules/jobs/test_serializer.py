"""잡 페이로드 직렬화 테스트."""
import json
from datetime import datetime

import pytest

from modules.jobs.backlink_refresh_payload import BacklinkRefreshJobPayload
from modules.jobs.cache_purge_payload import CachePurgeJobPayload
from modules.jobs.category_refresh_payload import CategoryRefreshJobPayload
from modules.jobs.recent_changes_payload import RecentChangesJobPayload
from modules.jobs.serializer import (
    JobPayloadSerializer,
    PayloadRegistry,
    UnknownPayloadTypeError,
)


class TestPayloadRegistry:
    """페이로드 레지스트리 테스트."""

    def test_registers_payload_class(self):
        """페이로드 클래스를 등록할 수 있다."""
        registry = PayloadRegistry()

        registry.register("cache.purge", CachePurgeJobPayload)

        assert registry.is_registered("cache.purge")

    def test_retrieves_registered_payload_class(self):
        """등록된 페이로드 클래스를 조회할 수 있다."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)

        payload_class = registry.get("cache.purge")

        assert payload_class is CachePurgeJobPayload

    def test_raises_on_duplicate_registration(self):
        """동일한 job_type으로 중복 등록을 거부한다."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)

        with pytest.raises(ValueError):
            registry.register("cache.purge", CachePurgeJobPayload)

    def test_raises_on_unregistered_lookup(self):
        """등록되지 않은 job_type을 조회하면 예외를 발생한다."""
        registry = PayloadRegistry()

        with pytest.raises(UnknownPayloadTypeError):
            registry.get("unknown.job")

    def test_is_registered_returns_false_for_unknown(self):
        """등록되지 않은 job_type은 False를 반환한다."""
        registry = PayloadRegistry()

        assert registry.is_registered("unknown.job") is False


class TestJobPayloadSerializerCachePurge:
    """캐시 퍼지 페이로드 직렬화/역직렬화 테스트."""

    def test_serializes_scoped_cache_purge_payload(self):
        """스코프 지정 캐시 퍼지 페이로드를 직렬화할 수 있다."""
        payload = CachePurgeJobPayload(source="== Title ==", parser_version="2.0.0")

        result = JobPayloadSerializer.serialize(payload)

        data = json.loads(result)
        assert data["job_type"] == "cache.purge"
        assert data["data"]["source"] == "== Title =="
        assert data["data"]["parser_version"] == "2.0.0"
        assert data["data"]["purge_all"] is False

    def test_serializes_purge_all_cache_payload(self):
        """전체 캐시 퍼지 페이로드를 직렬화할 수 있다."""
        payload = CachePurgeJobPayload(purge_all=True)

        result = JobPayloadSerializer.serialize(payload)

        data = json.loads(result)
        assert data["job_type"] == "cache.purge"
        assert data["data"]["purge_all"] is True
        assert data["data"]["source"] is None

    def test_deserializes_scoped_cache_purge_payload(self):
        """스코프 지정 캐시 퍼지 페이로드를 역직렬화할 수 있다."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)
        json_str = json.dumps({
            "job_type": "cache.purge",
            "data": {
                "source": "doc",
                "parser_version": "1.5.0",
                "purge_all": False,
            },
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.source == "doc"
        assert payload.parser_version == "1.5.0"
        assert payload.purge_all is False

    def test_deserializes_purge_all_cache_payload(self):
        """전체 캐시 퍼지 페이로드를 역직렬화할 수 있다."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)
        json_str = json.dumps({
            "job_type": "cache.purge",
            "data": {"purge_all": True},
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.purge_all is True
        assert payload.source is None

    def test_roundtrip_scoped_cache_purge(self):
        """스코프 지정 캐시 퍼지 페이로드 왕복 변환."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)
        original = CachePurgeJobPayload(source="text", parser_version="3.0.0")

        serialized = JobPayloadSerializer.serialize(original)
        deserialized = JobPayloadSerializer.deserialize(serialized, registry)

        assert deserialized.source == original.source
        assert deserialized.parser_version == original.parser_version
        assert deserialized.purge_all == original.purge_all

    def test_roundtrip_purge_all_cache(self):
        """전체 캐시 퍼지 페이로드 왕복 변환."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)
        original = CachePurgeJobPayload(purge_all=True)

        serialized = JobPayloadSerializer.serialize(original)
        deserialized = JobPayloadSerializer.deserialize(serialized, registry)

        assert deserialized.purge_all == original.purge_all
        assert deserialized.source == original.source


class TestJobPayloadSerializerBacklinkRefresh:
    """백링크 갱신 페이로드 직렬화/역직렬화 테스트."""

    def test_serializes_backlink_refresh_payload(self):
        """백링크 갱신 페이로드를 직렬화할 수 있다."""
        payload = BacklinkRefreshJobPayload(page_name="Test Page")

        result = JobPayloadSerializer.serialize(payload)

        data = json.loads(result)
        assert data["job_type"] == "backlink.refresh"
        assert data["data"]["page_name"] == "Test Page"

    def test_deserializes_backlink_refresh_payload(self):
        """백링크 갱신 페이로드를 역직렬화할 수 있다."""
        registry = PayloadRegistry()
        registry.register("backlink.refresh", BacklinkRefreshJobPayload)
        json_str = json.dumps({
            "job_type": "backlink.refresh",
            "data": {"page_name": "Test Page"},
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.page_name == "Test Page"

    def test_roundtrip_backlink_refresh(self):
        """백링크 갱신 페이로드 왕복 변환."""
        registry = PayloadRegistry()
        registry.register("backlink.refresh", BacklinkRefreshJobPayload)
        original = BacklinkRefreshJobPayload(page_name="Sample")

        serialized = JobPayloadSerializer.serialize(original)
        deserialized = JobPayloadSerializer.deserialize(serialized, registry)

        assert deserialized.page_name == original.page_name


class TestJobPayloadSerializerCategoryRefresh:
    """카테고리 갱신 페이로드 직렬화/역직렬화 테스트."""

    def test_serializes_category_refresh_payload(self):
        """카테고리 갱신 페이로드를 직렬화할 수 있다."""
        payload = CategoryRefreshJobPayload(category_name="Tech")

        result = JobPayloadSerializer.serialize(payload)

        data = json.loads(result)
        assert data["job_type"] == "category.refresh"
        assert data["data"]["category_name"] == "Tech"

    def test_deserializes_category_refresh_payload(self):
        """카테고리 갱신 페이로드를 역직렬화할 수 있다."""
        registry = PayloadRegistry()
        registry.register("category.refresh", CategoryRefreshJobPayload)
        json_str = json.dumps({
            "job_type": "category.refresh",
            "data": {"category_name": "Tech"},
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.category_name == "Tech"

    def test_roundtrip_category_refresh(self):
        """카테고리 갱신 페이로드 왕복 변환."""
        registry = PayloadRegistry()
        registry.register("category.refresh", CategoryRefreshJobPayload)
        original = CategoryRefreshJobPayload(category_name="Science")

        serialized = JobPayloadSerializer.serialize(original)
        deserialized = JobPayloadSerializer.deserialize(serialized, registry)

        assert deserialized.category_name == original.category_name


class TestJobPayloadSerializerRecentChanges:
    """최근 변경 내역 페이로드 직렬화/역직렬화 테스트."""

    def test_serializes_recent_changes_payload(self):
        """최근 변경 내역 페이로드를 직렬화할 수 있다."""
        occurred_at = datetime(2025, 7, 2, 12, 0, 0)
        payload = RecentChangesJobPayload(
            page_name="Document",
            author_id="user123",
            occurred_at=occurred_at,
            summary="Updated content",
        )

        result = JobPayloadSerializer.serialize(payload)

        data = json.loads(result)
        assert data["job_type"] == "recent_changes.record"
        assert data["data"]["page_name"] == "Document"
        assert data["data"]["author_id"] == "user123"
        assert data["data"]["summary"] == "Updated content"
        assert data["data"]["occurred_at"] == "2025-07-02T12:00:00"

    def test_deserializes_recent_changes_payload(self):
        """최근 변경 내역 페이로드를 역직렬화할 수 있다."""
        registry = PayloadRegistry()
        registry.register("recent_changes.record", RecentChangesJobPayload)
        json_str = json.dumps({
            "job_type": "recent_changes.record",
            "data": {
                "page_name": "Document",
                "author_id": "user123",
                "occurred_at": "2025-07-02T12:00:00",
                "summary": "Updated content",
            },
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.page_name == "Document"
        assert payload.author_id == "user123"
        assert payload.occurred_at == datetime(2025, 7, 2, 12, 0, 0)
        assert payload.summary == "Updated content"

    def test_deserializes_recent_changes_without_summary(self):
        """최근 변경 내역 페이로드 역직렬화 (summary 생략)."""
        registry = PayloadRegistry()
        registry.register("recent_changes.record", RecentChangesJobPayload)
        json_str = json.dumps({
            "job_type": "recent_changes.record",
            "data": {
                "page_name": "Document",
                "author_id": "user123",
                "occurred_at": "2025-07-02T12:00:00",
            },
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert payload.summary == ""

    def test_roundtrip_recent_changes(self):
        """최근 변경 내역 페이로드 왕복 변환."""
        registry = PayloadRegistry()
        registry.register("recent_changes.record", RecentChangesJobPayload)
        occurred_at = datetime(2025, 7, 1, 10, 30, 0)
        original = RecentChangesJobPayload(
            page_name="Wiki",
            author_id="alice",
            occurred_at=occurred_at,
            summary="Minor fix",
        )

        serialized = JobPayloadSerializer.serialize(original)
        deserialized = JobPayloadSerializer.deserialize(serialized, registry)

        assert deserialized.page_name == original.page_name
        assert deserialized.author_id == original.author_id
        assert deserialized.occurred_at == original.occurred_at
        assert deserialized.summary == original.summary


class TestJobPayloadSerializerErrors:
    """직렬화/역직렬화 에러 처리 테스트."""

    def test_deserialize_raises_on_unknown_job_type(self):
        """미등록 job_type 역직렬화 시 예외 발생."""
        registry = PayloadRegistry()
        json_str = json.dumps({
            "job_type": "unknown.type",
            "data": {},
        })

        with pytest.raises(UnknownPayloadTypeError):
            JobPayloadSerializer.deserialize(json_str, registry)

    def test_deserialize_with_multiple_registered_types(self):
        """여러 타입이 등록된 레지스트리에서 올바른 타입 역직렬화."""
        registry = PayloadRegistry()
        registry.register("cache.purge", CachePurgeJobPayload)
        registry.register("backlink.refresh", BacklinkRefreshJobPayload)

        json_str = json.dumps({
            "job_type": "backlink.refresh",
            "data": {"page_name": "Test"},
        })

        payload = JobPayloadSerializer.deserialize(json_str, registry)

        assert isinstance(payload, BacklinkRefreshJobPayload)
        assert payload.page_name == "Test"
