"""잡 모듈 테스트 픽스처."""
import pytest

from tests.modules.jobs.fixtures import (
    AlwaysFailingHandler,
    FailingHandler,
    FailingPayloadRecordingHandler,
    PayloadRecordingHandler,
    RaisingHandler,
    SamplePayload,
    SucceedingHandler,
    SucceedingWithoutDataHandler,
)


# === 페이로드 픽스처 ===

@pytest.fixture
def sample_payload():
    """기본 테스트 페이로드."""
    return SamplePayload()


@pytest.fixture
def sample_payload_with_name():
    """이름이 지정된 테스트 페이로드."""
    return SamplePayload(name="custom")


# === 성공 핸들러 픽스처 ===

@pytest.fixture
def succeeding_handler():
    """항상 성공하는 핸들러."""
    return SucceedingHandler()


@pytest.fixture
def succeeding_without_data_handler():
    """데이터 없이 성공하는 핸들러."""
    return SucceedingWithoutDataHandler()


# === 페이로드 기록 핸들러 픽스처 ===

@pytest.fixture
def payload_recording_handler():
    """페이로드를 기록하는 핸들러."""
    return PayloadRecordingHandler()


# === 실패 핸들러 픽스처 ===

@pytest.fixture
def failing_handler():
    """항상 실패하는 핸들러."""
    return FailingHandler()


@pytest.fixture
def failing_payload_recording_handler():
    """페이로드를 기록하면서 실패하는 핸들러."""
    return FailingPayloadRecordingHandler()


@pytest.fixture
def always_failing_handler():
    """모든 시도에서 실패하는 핸들러."""
    return AlwaysFailingHandler()


# === 예외 발생 핸들러 픽스처 ===

@pytest.fixture
def raising_handler():
    """예외를 발생하는 핸들러."""
    return RaisingHandler()


__all__ = [
    "sample_payload",
    "sample_payload_with_name",
    "succeeding_handler",
    "succeeding_without_data_handler",
    "payload_recording_handler",
    "failing_handler",
    "failing_payload_recording_handler",
    "always_failing_handler",
    "raising_handler",
]
