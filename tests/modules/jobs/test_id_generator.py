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

    def test_generated_id_is_non_empty_string(self):
        """생성된 ID가 비어있지 않은 문자열인지 확인한다."""
        job_id = generate_job_id()

        assert job_id
        assert job_id.strip()
