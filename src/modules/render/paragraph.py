"""평문 문단 렌더러."""

from modules.render.escape import escape_html


def render_plain_paragraph(content: str) -> str:
    """
    평문 문단을 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <p> 태그로 감싼다.

    Args:
        content: 문단의 텍스트 내용

    Returns:
        HTML로 렌더링된 문단 ('<p>...</p>' 형태)
    """
    escaped_content = escape_html(content)
    return f"<p>{escaped_content}</p>"
