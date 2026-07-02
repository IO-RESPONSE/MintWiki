"""잡 모듈 테스트 픽스처 세트."""
from modules.jobs import JobHandler, JobPayload, JobResult


# === 기본 페이로드 ===

class SamplePayload(JobPayload):
    """가장 간단한 테스트용 페이로드."""

    def __init__(self, name: str = "sample"):
        self.name = name

    @property
    def job_type(self) -> str:
        return "sample.job"


# === 성공 핸들러 ===

class SucceedingHandler(JobHandler):
    """항상 성공하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok(data={"handled": payload.job_type})


class SucceedingWithoutDataHandler(JobHandler):
    """데이터 없이 성공하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok()


# === 페이로드 기록 핸들러 ===

class PayloadRecordingHandler(JobHandler):
    """run()이 전달한 페이로드를 기록해 검증할 수 있게 한다."""

    def __init__(self):
        self.received_payload = None

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        self.received_payload = payload
        return JobResult.ok()


# === 실패 핸들러 ===

class FailingHandler(JobHandler):
    """항상 실패하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("처리 실패")


class FailingPayloadRecordingHandler(JobHandler):
    """실패 응답을 반환하면서도 run()이 전달한 페이로드를 기록해 검증할 수 있게 한다."""

    def __init__(self):
        self.received_payload = None

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        self.received_payload = payload
        return JobResult.fail("처리 실패")


class AlwaysFailingHandler(JobHandler):
    """모든 시도에서 실패하는 핸들러. 최대 시도 소진 시나리오를 재현한다."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("처리 실패")


# === 예외 발생 핸들러 ===

class RaisingHandler(JobHandler):
    """예외를 발생하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        raise RuntimeError("예상치 못한 오류")


__all__ = [
    "SamplePayload",
    "SucceedingHandler",
    "SucceedingWithoutDataHandler",
    "PayloadRecordingHandler",
    "FailingHandler",
    "FailingPayloadRecordingHandler",
    "AlwaysFailingHandler",
    "RaisingHandler",
]
