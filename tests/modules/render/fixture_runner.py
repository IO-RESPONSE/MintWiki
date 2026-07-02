"""렌더 모듈 픽스처 테스트 러너."""
from pathlib import Path
from typing import Callable, Any, Dict, List, Optional


class FixtureRunner:
    """픽스처 파일을 사용하여 렌더 함수를 테스트하는 러너."""

    def __init__(self, fixture_dir: Optional[str] = None):
        """
        픽스처 러너를 초기화한다.

        Args:
            fixture_dir: 픽스처 파일이 있는 디렉토리 경로. 기본값은 fixtures 디렉토리.
        """
        if fixture_dir is None:
            fixture_dir = Path(__file__).parent / "fixtures"
        self.fixture_dir = Path(fixture_dir)

    def load_fixture(self, filename: str) -> str:
        """
        픽스처 파일을 로드한다.

        Args:
            filename: 로드할 픽스처 파일 이름

        Returns:
            픽스처 파일의 내용

        Raises:
            FileNotFoundError: 픽스처 파일을 찾을 수 없는 경우
        """
        fixture_path = self.fixture_dir / filename

        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

        with open(fixture_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_fixtures(self) -> List[str]:
        """
        사용 가능한 모든 픽스처 파일을 나열한다.

        Returns:
            픽스처 파일명 목록 (알파벳 순서)
        """
        fixtures = [
            f.name
            for f in self.fixture_dir.iterdir()
            if f.is_file() and f.suffix == ".html"
        ]
        return sorted(fixtures)

    def run_fixture(
        self,
        fixture_filename: str,
        render_func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        픽스처 파일에 대해 렌더 함수를 실행하고 결과를 비교한다.

        Args:
            fixture_filename: 픽스처 파일 이름
            render_func: 렌더링 함수
            *args: 렌더 함수에 전달할 위치 인자
            **kwargs: 렌더 함수에 전달할 키워드 인자

        Returns:
            렌더 결과와 픽스처가 일치하면 True, 아니면 False

        Raises:
            FileNotFoundError: 픽스처 파일을 찾을 수 없는 경우
        """
        expected = self.load_fixture(fixture_filename)
        actual = render_func(*args, **kwargs)
        return actual == expected

    def run_fixture_with_comparison(
        self,
        fixture_filename: str,
        render_func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        픽스처 파일에 대해 렌더 함수를 실행하고 상세한 비교 결과를 반환한다.

        Args:
            fixture_filename: 픽스처 파일 이름
            render_func: 렌더링 함수
            *args: 렌더 함수에 전달할 위치 인자
            **kwargs: 렌더 함수에 전달할 키워드 인자

        Returns:
            다음 정보를 포함하는 딕셔너리:
                - success: 테스트 통과 여부 (bool)
                - expected: 픽스처의 예상 출력 (str)
                - actual: 렌더 함수의 실제 출력 (str)
                - fixture_file: 사용된 픽스처 파일명 (str)
                - mismatch: 불일치 정보 (str, 실패시만 포함)

        Raises:
            FileNotFoundError: 픽스처 파일을 찾을 수 없는 경우
        """
        expected = self.load_fixture(fixture_filename)
        actual = render_func(*args, **kwargs)
        success = actual == expected

        result = {
            "success": success,
            "expected": expected,
            "actual": actual,
            "fixture_file": fixture_filename,
        }

        if not success:
            result["mismatch"] = (
                f"Expected:\n{expected!r}\n\nActual:\n{actual!r}"
            )

        return result


__all__ = ["FixtureRunner"]
