"""잡 ID 생성기 테스트."""
import uuid
from modules.jobs.id_generator import generate_job_id


class TestGenerateJobId:
    """generate_job_id가 유효한 ID를 생성하는지 확인한다."""

    def test_generates_valid_uuid_string(self):
        """생성된 ID가 유효한 UUID 형식의 문자열인지 확인한다."""
        job_id = generate_job_id()

        # UUID 형식의 문자열인지 확인 (예외가 발생하지 않으면 유효)
        uuid.UUID(job_id)
        assert isinstance(job_id, str)

    def test_generates_unique_ids(self):
        """여러 번 호출할 때마다 다른 ID를 생성하는지 확인한다."""
        id1 = generate_job_id()
        id2 = generate_job_id()
        id3 = generate_job_id()

        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_generates_unique_ids_large_sample(self):
        """대량 생성 시 모든 ID가 고유한지 확인한다."""
        # 1000개의 ID를 생성하여 중복이 없는지 확인
        num_ids = 1000
        generated_ids = [generate_job_id() for _ in range(num_ids)]

        # 중복 없이 모두 고유해야 함
        unique_ids = set(generated_ids)
        assert len(unique_ids) == num_ids, f"중복된 ID 감지: {num_ids}개 생성, {len(unique_ids)}개 고유"

    def test_generated_id_is_non_empty_string(self):
        """생성된 ID가 비어있지 않은 문자열인지 확인한다."""
        job_id = generate_job_id()

        assert job_id
        assert job_id.strip()
