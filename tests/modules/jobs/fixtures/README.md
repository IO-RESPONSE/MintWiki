# Job Test Fixtures

이 디렉토리는 잡 모듈의 테스트에서 사용할 수 있는 공통 테스트 픽스처를 포함합니다.

## 제공되는 픽스처

### 페이로드

- `SamplePayload` - 가장 간단한 테스트 페이로드. job_type은 "sample.job"

### 핸들러

#### 성공 핸들러

- `SucceedingHandler` - 항상 성공하는 핸들러 (데이터 포함)
- `SucceedingWithoutDataHandler` - 데이터 없이 성공하는 핸들러

#### 실패 핸들러

- `FailingHandler` - 항상 실패하는 핸들러
- `AlwaysFailingHandler` - 모든 시도에서 실패하는 핸들러 (재시도 소진 시나리오용)

#### 특수 핸들러

- `PayloadRecordingHandler` - 성공 응답을 반환하면서 받은 페이로드를 기록
- `FailingPayloadRecordingHandler` - 실패 응답을 반환하면서 받은 페이로드를 기록

#### 예외 발생 핸들러

- `RaisingHandler` - 예외를 발생하는 핸들러

## 사용 방법

### 직접 import 사용

```python
from tests.modules.jobs.fixtures import (
    SamplePayload,
    SucceedingHandler,
    FailingHandler,
)

def test_runner_with_succeeding_handler():
    runner = SyncJobRunner()
    handler = SucceedingHandler()
    payload = SamplePayload()
    
    outcome = runner.run(handler, payload)
    
    assert outcome.status == JobStatus.SUCCEEDED
```

### pytest fixture 사용

conftest.py에서 제공하는 pytest fixture를 사용할 수 있습니다:

```python
def test_with_fixture(sample_payload, succeeding_handler):
    """pytest fixture를 사용한 테스트."""
    runner = SyncJobRunner()
    outcome = runner.run(succeeding_handler, sample_payload)
    
    assert outcome.status == JobStatus.SUCCEEDED
```

## 이용 가능한 pytest Fixtures

- `sample_payload` - 기본 테스트 페이로드
- `sample_payload_with_name` - 이름이 지정된 테스트 페이로드
- `succeeding_handler` - 성공하는 핸들러
- `succeeding_without_data_handler` - 데이터 없이 성공하는 핸들러
- `payload_recording_handler` - 페이로드를 기록하는 핸들러
- `failing_handler` - 실패하는 핸들러
- `failing_payload_recording_handler` - 페이로드를 기록하면서 실패하는 핸들러
- `always_failing_handler` - 항상 실패하는 핸들러
- `raising_handler` - 예외를 발생하는 핸들러
