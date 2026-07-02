"""검색 오류 처리 모델 테스트."""
from modules.search.errors import SearchServiceError


class TestSearchServiceErrorConstruction:
    """SearchServiceError 생성 테스트."""

    def test_stores_operation_and_original_error(self):
        """operation과 original_error를 그대로 보관한다."""
        original = ValueError("연결 실패")

        error = SearchServiceError("search", original)

        assert error.operation == "search"
        assert error.original_error is original

    def test_message_includes_operation_and_original_error(self):
        """오류 메시지에 작업 이름과 원본 예외 내용이 포함된다."""
        original = ValueError("연결 실패")

        error = SearchServiceError("index", original)

        assert "index" in str(error)
        assert "연결 실패" in str(error)

    def test_is_exception_subclass(self):
        """SearchServiceError는 Exception의 하위 클래스다."""
        assert issubclass(SearchServiceError, Exception)

    def test_can_be_raised_and_caught(self):
        """일반적인 예외처럼 raise/except로 다룰 수 있다."""
        original = RuntimeError("어댑터 오류")

        try:
            raise SearchServiceError("delete", original)
        except SearchServiceError as caught:
            assert caught.operation == "delete"
            assert caught.original_error is original
        else:
            assert False, "SearchServiceError가 발생해야 한다"
