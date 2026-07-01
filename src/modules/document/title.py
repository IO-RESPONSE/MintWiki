"""제목 정규화 유틸리티."""


class EmptyTitleError(Exception):
    """제목이 비어있을 때 발생."""

    pass


def normalize_title(title: str) -> str:
    """
    문서 제목을 정규화한다.

    주변 공백을 제거하고 내부 공백을 단일 공백으로 축소한다.

    Args:
        title: 정규화할 제목

    Returns:
        정규화된 제목

    Raises:
        EmptyTitleError: 제목이 비어있거나 공백만 있는 경우
    """
    normalized = " ".join(title.split())

    if not normalized:
        raise EmptyTitleError("제목은 비어있을 수 없습니다")

    return normalized
