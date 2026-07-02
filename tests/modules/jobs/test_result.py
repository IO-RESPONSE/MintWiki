"""잡 실행 결과 모델 테스트."""
import pytest

from modules.jobs import InvalidJobResultError, JobResult


class TestJobResultSuccess:
    """성공한 잡 실행 결과의 동작을 검증한다."""

    def test_ok_factory_sets_success_and_data(self):
        """JobResult.ok()는 success=True와 전달한 data를 그대로 담는다."""
        result = JobResult.ok(data={"indexed": 3})

        assert result.success is True
        assert result.data == {"indexed": 3}
        assert result.error is None

    def test_ok_factory_without_data_defaults_to_none(self):
        """data 없이 생성해도 성공 결과를 만들 수 있다."""
        result = JobResult.ok()

        assert result.success is True
        assert result.data is None

    def test_direct_construction_with_success_true(self):
        """생성자를 직접 사용해도 동일한 성공 결과를 만들 수 있다."""
        result = JobResult(success=True, data="done")

        assert result.success is True
        assert result.data == "done"
        assert result.error is None


class TestJobResultFailure:
    """실패한 잡 실행 결과의 동작을 검증한다."""

    def test_fail_factory_sets_success_false_and_error(self):
        """JobResult.fail()은 success=False와 전달한 error를 그대로 담는다."""
        result = JobResult.fail("색인 대상 문서를 찾을 수 없습니다")

        assert result.success is False
        assert result.error == "색인 대상 문서를 찾을 수 없습니다"
        assert result.data is None


class TestJobResultInvariants:
    """success와 error/data 조합에 대한 불변식을 검증한다."""

    def test_success_with_error_raises(self):
        """성공 결과에 error를 함께 넘기면 예외가 발생한다."""
        with pytest.raises(InvalidJobResultError):
            JobResult(success=True, error="이럴 수 없음")

    def test_failure_without_error_raises(self):
        """실패 결과인데 error가 없으면 예외가 발생한다."""
        with pytest.raises(InvalidJobResultError):
            JobResult(success=False)
