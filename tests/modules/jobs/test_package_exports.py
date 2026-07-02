"""jobs 패키지 export 테스트."""
import modules.jobs as jobs


class TestJobsPackageExports:
    """jobs 패키지가 정상적으로 import 가능한지 검증한다."""

    def test_package_is_importable(self):
        """jobs 패키지를 import할 수 있다."""
        assert jobs is not None

    def test_all_matches_declared_exports(self):
        """__all__ 에 선언된 이름이 실제 모듈 속성으로 존재한다.

        잡 상태, 핸들러, 실행기 등 나머지 계약은 후속 태스크에서
        추가되므로, 현재는 공통 페이로드 기반 클래스와 결과 값
        객체만 검증한다.
        """
        assert jobs.__all__ == ["JobPayload", "JobResult", "InvalidJobResultError"]
        for name in jobs.__all__:
            assert hasattr(jobs, name)
