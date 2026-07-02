"""JobMetricsHook 테스트."""
from datetime import datetime, timedelta, timezone

import pytest

from modules.jobs.job_metrics_hook import JobMetric, JobMetricsHook


class TestJobMetric:
    """JobMetric 테스트."""

    def test_create_metric(self):
        """메트릭을 생성할 수 있다."""
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)

        metric = JobMetric(
            job_type="test.job",
            succeeded=True,
            started_at=started,
            completed_at=completed,
        )

        assert metric.job_type == "test.job"
        assert metric.succeeded is True
        assert metric.started_at == started
        assert metric.completed_at == completed
        assert metric.metadata == {}

    def test_create_metric_with_metadata(self):
        """메타데이터를 포함하는 메트릭을 생성할 수 있다."""
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)
        metadata = {"retry_count": 1, "queue_name": "default"}

        metric = JobMetric(
            job_type="test.job",
            succeeded=True,
            started_at=started,
            completed_at=completed,
            metadata=metadata,
        )

        assert metric.metadata == {"retry_count": 1, "queue_name": "default"}

    def test_duration_seconds(self):
        """실행 시간을 초 단위로 계산할 수 있다."""
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 10, tzinfo=timezone.utc)

        metric = JobMetric(
            job_type="test.job",
            succeeded=True,
            started_at=started,
            completed_at=completed,
        )

        assert metric.duration_seconds() == 10.0

    def test_duration_seconds_with_fractional_seconds(self):
        """실행 시간을 소수점 초로 계산할 수 있다."""
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = started + timedelta(seconds=5, milliseconds=500)

        metric = JobMetric(
            job_type="test.job",
            succeeded=True,
            started_at=started,
            completed_at=completed,
        )

        assert metric.duration_seconds() == pytest.approx(5.5)

    def test_failed_metric(self):
        """실패한 잡의 메트릭을 생성할 수 있다."""
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)

        metric = JobMetric(
            job_type="test.job",
            succeeded=False,
            started_at=started,
            completed_at=completed,
        )

        assert metric.succeeded is False


class TestJobMetricsHook:
    """JobMetricsHook 테스트."""

    def test_create_hook(self):
        """메트릭 훅을 생성할 수 있다."""
        hook = JobMetricsHook()
        assert hook.metrics() == []

    def test_record_job_metric(self):
        """잡 메트릭을 기록할 수 있다."""
        hook = JobMetricsHook()
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)

        metric = hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=started,
            completed_at=completed,
        )

        assert metric.job_type == "cache.purge"
        assert metric.succeeded is True
        assert len(hook.metrics()) == 1

    def test_record_multiple_metrics(self):
        """여러 개의 메트릭을 기록할 수 있다."""
        hook = JobMetricsHook()
        started1 = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed1 = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)
        started2 = datetime(2026, 7, 2, 12, 1, 0, tzinfo=timezone.utc)
        completed2 = datetime(2026, 7, 2, 12, 1, 3, tzinfo=timezone.utc)

        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=started1,
            completed_at=completed1,
        )
        hook.record_job_metric(
            job_type="search.index",
            succeeded=False,
            started_at=started2,
            completed_at=completed2,
        )

        metrics = hook.metrics()
        assert len(metrics) == 2
        assert metrics[0].job_type == "cache.purge"
        assert metrics[1].job_type == "search.index"

    def test_metrics_returns_copy(self):
        """metrics()는 메트릭 목록의 복사본을 반환한다."""
        hook = JobMetricsHook()
        started = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 7, 2, 12, 0, 5, tzinfo=timezone.utc)

        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=started,
            completed_at=completed,
        )

        metrics1 = hook.metrics()
        metrics2 = hook.metrics()

        assert metrics1 is not metrics2
        assert len(metrics1) == len(metrics2)

    def test_metrics_by_type(self):
        """특정 잡 타입의 메트릭만 필터링할 수 있다."""
        hook = JobMetricsHook()
        now = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
        )
        hook.record_job_metric(
            job_type="search.index",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=10),
        )
        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=False,
            started_at=now,
            completed_at=now + timedelta(seconds=3),
        )

        cache_metrics = hook.metrics_by_type("cache.purge")
        assert len(cache_metrics) == 2
        assert all(m.job_type == "cache.purge" for m in cache_metrics)

    def test_metrics_by_type_empty(self):
        """존재하지 않는 잡 타입을 요청하면 빈 목록을 반환한다."""
        hook = JobMetricsHook()
        now = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
        )

        metrics = hook.metrics_by_type("nonexistent.job")
        assert metrics == []

    def test_record_with_metadata(self):
        """메타데이터를 포함하여 메트릭을 기록할 수 있다."""
        hook = JobMetricsHook()
        now = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        metadata = {"retry_count": 2, "queue": "critical"}

        metric = hook.record_job_metric(
            job_type="search.index",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
            metadata=metadata,
        )

        assert metric.metadata == {"retry_count": 2, "queue": "critical"}

    def test_clear_metrics(self):
        """누적된 메트릭을 모두 삭제할 수 있다."""
        hook = JobMetricsHook()
        now = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

        hook.record_job_metric(
            job_type="cache.purge",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
        )
        hook.record_job_metric(
            job_type="search.index",
            succeeded=True,
            started_at=now,
            completed_at=now + timedelta(seconds=10),
        )

        assert len(hook.metrics()) == 2

        hook.clear_metrics()

        assert len(hook.metrics()) == 0

    def test_metrics_order_preserved(self):
        """메트릭은 기록 순서대로 반환된다."""
        hook = JobMetricsHook()
        timestamps = []

        for i in range(5):
            now = datetime(2026, 7, 2, 12, 0, i, tzinfo=timezone.utc)
            timestamps.append(now)
            hook.record_job_metric(
                job_type="test.job",
                succeeded=True,
                started_at=now,
                completed_at=now + timedelta(seconds=1),
            )

        metrics = hook.metrics()
        for i, metric in enumerate(metrics):
            assert metric.started_at == timestamps[i]
