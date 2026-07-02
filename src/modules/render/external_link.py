"""외부 링크 렌더러."""

from typing import Optional
from modules.render.escape import escape_html


def render_external_link(url: str, label: Optional[str] = None) -> str:
    """
    외부 링크를 HTML로 렌더링한다.

    XSS 공격과 보안 위협을 방지하기 위해 URL과 레이블을 이스케이프한 후 <a> 태그로 감싼다.
    외부 링크에는 XSS 및 성능 관련 보안 위협을 완화하기 위해 rel="noopener noreferrer" 속성을 추가한다.

    Args:
        url: 링크할 URL
        label: 링크 텍스트 (생략하면 URL 사용)

    Returns:
        HTML로 렌더링된 외부 링크 ('<a href="..." rel="noopener noreferrer">...</a>' 형태)
    """
    # URL을 이스케이프하여 href 속성에 사용
    escaped_url = escape_html(url)

    # 레이블 설정: 레이블이 없으면 URL 사용
    display_text = label if label is not None else url
    escaped_label = escape_html(display_text)

    return f'<a href="{escaped_url}" rel="noopener noreferrer">{escaped_label}</a>'
