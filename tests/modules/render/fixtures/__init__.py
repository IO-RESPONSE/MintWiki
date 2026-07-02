"""렌더 모듈 HTML 스냅샷 픽스처."""
import os
from pathlib import Path


def load_fixture(filename: str) -> str:
    """
    픽스처 파일을 로드한다.

    Args:
        filename: 로드할 픽스처 파일 이름 (예: 'simple_paragraph.html')

    Returns:
        픽스처 파일의 내용
    """
    fixture_dir = Path(__file__).parent
    fixture_path = fixture_dir / filename

    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


def list_fixtures() -> list[str]:
    """
    사용 가능한 모든 픽스처 파일을 나열한다.

    Returns:
        픽스처 파일명 목록
    """
    fixture_dir = Path(__file__).parent
    return [
        f.name
        for f in fixture_dir.iterdir()
        if f.is_file() and f.suffix == ".html"
    ]


__all__ = ["load_fixture", "list_fixtures"]
