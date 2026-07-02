"""코드 블록 렌더러."""

from modules.render.escape import escape_html


def render_code_block(content: str) -> str:
    """
    코드 블록을 HTML로 렌더링한다.

    코드 블록 내의 콘텐츠는 위키 마크업이 해석되지 않은 그대로이다.
    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 <pre><code> 태그로 감싼다.

    Args:
        content: 코드 블록의 리터럴 텍스트 내용

    Returns:
        HTML로 렌더링된 코드 블록 ('<pre><code>...</code></pre>' 형태)
    """
    escaped_content = escape_html(content)
    return f"<pre><code>{escaped_content}</code></pre>"
