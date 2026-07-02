"""검색 오류 처리 도메인 모델."""


class SearchServiceError(Exception):
    """
    검색 어댑터에서 발생한 예외를 감싸는 서비스 계층 오류.

    SearchAdapter 구현체(외부 검색 엔진 클라이언트 등)가 예상치 못한 예외를
    던졌을 때, 호출자가 구체적인 어댑터 구현과 무관하게 하나의 오류 타입만
    처리할 수 있도록 감싸는 역할을 한다. 어느 작업에서 실패했는지(operation)와
    원인이 된 원본 예외(original_error)를 함께 보관한다.

    SearchService는 어댑터 호출을 이 오류로 감싸 다시 던진다.
    """

    def __init__(self, operation: str, original_error: Exception):
        """
        서비스 오류를 생성한다.

        Args:
            operation: 오류가 발생한 검색 작업 이름 (예: "index", "search", "delete", "health_check")
            original_error: 어댑터가 던진 원본 예외
        """
        self.operation = operation
        self.original_error = original_error
        super().__init__(
            f"검색 {operation} 작업 중 오류가 발생했습니다: {original_error}"
        )
