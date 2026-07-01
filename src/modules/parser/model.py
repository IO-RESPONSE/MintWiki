"""파서 도메인 모델."""
from typing import Any, Dict, List, Optional, Literal


class ParserDiagnostic:
    """
    파싱 중 발견된 진단 정보를 나타내는 도메인 모델.

    파서가 구문 오류, 경고, 또는 기타 문제를 발견했을 때 생성되는 모델이다.
    각 진단은 심각도, 메시지, 위치 정보를 포함한다.
    """

    def __init__(
        self,
        message: str,
        severity: Literal["error", "warning", "info"],
        line: int,
        column: int,
        code: Optional[str] = None,
    ):
        """
        진단 정보를 생성한다.

        Args:
            message: 진단 메시지
            severity: 진단의 심각도 ("error", "warning", "info")
            line: 문제가 발생한 줄 번호 (1-indexed)
            column: 문제가 발생한 열 번호 (1-indexed)
            code: 진단 코드 (선택사항, 예: "E001", "W001")
        """
        self.message = message
        self.severity = severity
        self.line = line
        self.column = column
        self.code = code


class ParserResult:
    """
    파싱 결과를 나타내는 도메인 모델.

    파서가 소스 텍스트를 파싱한 후 생성하는 중간 표현이다.
    블록 단위의 파싱 결과와 추출된 메타데이터를 포함한다.
    """

    def __init__(
        self,
        blocks: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """
        파싱 결과를 생성한다.

        Args:
            blocks: 파싱된 블록 요소들의 리스트
            metadata: 파싱 중에 추출된 메타데이터
                - links: 문서에서 추출된 링크 목록
                - categories: 문서의 카테고리 목록
                - redirects: 리다이렉트 정보
                - headings: 제목 목록
                - transclusions: 트랜스클루전 목록
        """
        self.blocks = blocks
        self.metadata = metadata
