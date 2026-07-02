"""각주 섹션 렌더러."""

from typing import List
from modules.render.escape import escape_html


def render_footnotes_section(footnotes: List[str]) -> str:
    """
    각주 섹션을 HTML로 렌더링한다.

    각주들을 순서 있는 목록으로 렌더링하고, 각 각주에는 고유한 id 속성을 부여한다.
    XSS 공격을 방지하기 위해 각주 텍스트를 이스케이프한다.

    Args:
        footnotes: 각주 텍스트 리스트

    Returns:
        HTML로 렌더링된 각주 섹션
    """
    if not footnotes:
        return '<div class="footnotes-section"></div>'

    # 각 각주를 li 요소로 렌더링
    footnote_items = []
    for i, footnote in enumerate(footnotes, 1):
        escaped_footnote = escape_html(footnote)
        footnote_id = f"footnote-{i}"
        footnote_items.append(f'<li id="{footnote_id}">{escaped_footnote}</li>')

    # 각주들을 ol 태그로 감싸기
    footnotes_html = '\n'.join(footnote_items)
    return f'<div class="footnotes-section">\n<ol>\n{footnotes_html}\n</ol>\n</div>'
