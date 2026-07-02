"""nowiki 콘텐츠 렌더러."""

from modules.render.escape import escape_html


def render_nowiki(content: str) -> str:
    """
    nowiki 콘텐츠를 HTML로 렌더링한다.

    nowiki 블록 내의 콘텐츠는 위키 마크업이 해석되지 않은 그대로이다.
    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <code> 태그로 감싼다.

    Args:
        content: nowiki 블록의 리터럴 텍스트 내용

    Returns:
        HTML로 렌더링된 nowiki 콘텐츠 ('<code>...</code>' 형태)
    """
    escaped_content = escape_html(content)
    return f"<code>{escaped_content}</code>"
