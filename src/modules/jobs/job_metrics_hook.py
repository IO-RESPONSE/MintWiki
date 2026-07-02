"""잡 메트릭을 기록하는 훅."""
from datetime import datetime, timezone
from typing import Dict, List, Optional


class JobMetric:
    """
    단일 잡 실행의 메트릭 정보.

    잡 타입, 실행 상태, 실행 시간 등 잡 실행에 관련된 메트릭을 담는다.
    실제 메트릭 저장소 연동은 후속 태스크에서 다루며, 현재는 메모리에만
    누적한다.
    """

    def __init__(
        self,
        job_type: str,
        succeeded: bool,
        started_at: datetime,
        completed_at: datetime,
        metadata: Optional[Dict] = None,
    ):
        """
        잡 메트릭을 생성한다.

        Args:
            job_type: 잡의 종류를 식별하는 문자열
            succeeded: 잡 성공 여부
            started_at: 실행 시작 시각 (UTC)
            completed_at: 실행 종료 시각 (UTC)
            metadata: 추가 메트릭 정보 (선택사항)
        """
        self.job_type = job_type
        self.succeeded = succeeded
        self.started_at = started_at
        self.completed_at = completed_at
        self.metadata = metadata or {}

    def duration_seconds(self) -> float:
        """실행 시간을 초 단위로 반환한다."""
        delta = self.completed_at - self.started_at
        return delta.total_seconds()


class JobMetricsHook:
    """
    잡 실행 메트릭을 기록하는 훅.

    잡 실행 전후를 추적하여 메트릭(실행 시간, 성공/실패 등)을 기록한다.
    메트릭은 메모리에 누적되며, 메트릭 저장소 연동은 후속 태스크에서
    다루어진다. 이는 placeholder 구현이며, 실제 메트릭 수집 및 전송
    로직은 후속 태스크에서 추가된다.
    """

    def __init__(self):
        """메트릭 훅을 초기화한다."""
        self._metrics: List[JobMetric] = []

    def record_job_metric(
        self,
        job_type: str,
        succeeded: bool,
        started_at: datetime,
        completed_at: datetime,
        metadata: Optional[Dict] = None,
    ) -> JobMetric:
        """
        잡 실행 메트릭을 기록한다.

        Args:
            job_type: 잡의 종류를 식별하는 문자열
            succeeded: 잡 성공 여부
            started_at: 실행 시작 시각 (UTC)
            completed_at: 실행 종료 시각 (UTC)
            metadata: 추가 메트릭 정보 (선택사항)

        Returns:
            기록된 잡 메트릭
        """
        metric = JobMetric(
            job_type=job_type,
            succeeded=succeeded,
            started_at=started_at,
            completed_at=completed_at,
            metadata=metadata,
        )
        self._metrics.append(metric)
        return metric

    def metrics(self) -> List[JobMetric]:
        """지금까지 기록된 메트릭 목록을 시간 순서대로 반환한다."""
        return list(self._metrics)

    def metrics_by_type(self, job_type: str) -> List[JobMetric]:
        """특정 잡 타입의 메트릭만 필터링하여 반환한다."""
        return [m for m in self._metrics if m.job_type == job_type]

    def clear_metrics(self) -> None:
        """누적된 메트릭을 모두 삭제한다."""
        self._metrics.clear()


__all__ = ["JobMetric", "JobMetricsHook"]
