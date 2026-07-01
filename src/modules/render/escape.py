"""HTML 안전 이스케이프 헬퍼."""


def escape_html(text: str) -> str:
    """
    텍스트의 HTML 특수 문자를 이스케이프한다.

    XSS 공격을 방지하기 위해 HTML 렌더링에 사용되는 텍스트를 안전하게 이스케이프한다.

    Args:
        text: 이스케이프할 텍스트

    Returns:
        이스케이프된 텍스트
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
