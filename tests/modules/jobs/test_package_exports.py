"""jobs 패키지 export 테스트."""
import modules.jobs as jobs


class TestJobsPackageExports:
    """jobs 패키지가 정상적으로 import 가능한지 검증한다."""

    def test_package_is_importable(self):
        """jobs 패키지를 import할 수 있다."""
        assert jobs is not None

    def test_all_matches_declared_exports(self):
        """__all__ 에 선언된 이름이 실제 모듈 속성으로 존재한다.

        큐 적재 등 나머지 계약은 후속 태스크에서 추가되므로, 현재는 공통
        페이로드 기반 클래스, 결과 값 객체, 상태 열거형, 핸들러 인터페이스,
        동기 잡 실행기, 재시도 정책, 데드레터 모델, 잡 레지스트리, 캐시
        퍼지 페이로드/핸들러, 검색 색인 핸들러, 백링크 갱신 페이로드/
        placeholder 핸들러, 카테고리 갱신 페이로드/placeholder 핸들러,
        최근 변경 내역 페이로드/placeholder 핸들러, 잡 감사 이벤트
        모델, 잡 감사 기록기만 검증한다.
        """
        assert jobs.__all__ == [
            "JobAuditAction",
            "JobAuditEvent",
            "EmptyJobAuditEventIdError",
            "MissingJobTypeError",
            "InvalidJobAuditEventError",
            "JobAuditRecorder",
            "JobPayload",
            "JobResult",
            "InvalidJobResultError",
            "JobStatus",
            "JobHandler",
            "JobRunOutcome",
            "SyncJobRunner",
            "InvalidRetryPolicyError",
            "RetryPolicy",
            "InvalidDeadLetterError",
            "DeadLetter",
            "JobRegistry",
            "DuplicateJobTypeError",
            "UnknownJobTypeError",
            "CACHE_PURGE_JOB_TYPE",
            "CachePurgeJobPayload",
            "InvalidCachePurgeJobPayloadError",
            "CachePurgeJobHandler",
            "CATEGORY_REFRESH_JOB_TYPE",
            "CategoryRefreshJobPayload",
            "InvalidCategoryRefreshJobPayloadError",
            "CategoryRefreshJobHandler",
            "SEARCH_INDEX_JOB_TYPE",
            "SearchIndexJobHandler",
            "BACKLINK_REFRESH_JOB_TYPE",
            "BacklinkRefreshJobPayload",
            "InvalidBacklinkRefreshJobPayloadError",
            "BacklinkRefreshJobHandler",
            "RECENT_CHANGES_JOB_TYPE",
            "RecentChangesJobPayload",
            "InvalidRecentChangesJobPayloadError",
            "RecentChangesJobHandler",
        ]
        for name in jobs.__all__:
            assert hasattr(jobs, name)
