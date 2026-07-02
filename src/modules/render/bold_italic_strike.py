"""굵은, 이탤릭, 취소선 렌더러."""

from modules.render.escape import escape_html


def render_bold(text: str) -> str:
    """
    굵은 텍스트를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <b> 태그로 감싼다.

    Args:
        text: 굵게 표시할 텍스트

    Returns:
        HTML로 렌더링된 굵은 텍스트 ('<b>...</b>' 형태)
    """
    escaped_text = escape_html(text)
    return f"<b>{escaped_text}</b>"


def render_italic(text: str) -> str:
    """
    이탤릭 텍스트를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <i> 태그로 감싼다.

    Args:
        text: 이탤릭으로 표시할 텍스트

    Returns:
        HTML로 렌더링된 이탤릭 텍스트 ('<i>...</i>' 형태)
    """
    escaped_text = escape_html(text)
    return f"<i>{escaped_text}</i>"


def render_strike(text: str) -> str:
    """
    취소선 텍스트를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <s> 태그로 감싼다.

    Args:
        text: 취소선으로 표시할 텍스트

    Returns:
        HTML로 렌더링된 취소선 텍스트 ('<s>...</s>' 형태)
    """
    escaped_text = escape_html(text)
    return f"<s>{escaped_text}</s>"
