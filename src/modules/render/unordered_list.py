"""순서 없는 목록 렌더러."""

from typing import List, Dict, Any
from modules.render.escape import escape_html


def render_unordered_list_item(item: Dict[str, Any]) -> str:
    """
    순서 없는 목록의 항목을 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 텍스트를 이스케이프하고 중첩된 자식 항목을 재귀적으로 처리한다.

    Args:
        item: 목록 항목 딕셔너리
            - text: 항목의 텍스트 내용
            - children: 중첩된 자식 항목들의 리스트

    Returns:
        HTML로 렌더링된 목록 항목 ('<li>...</li>' 형태)
    """
    text = item.get("text", "")
    children = item.get("children", [])

    escaped_text = escape_html(text)
    html = f"<li>{escaped_text}"

    if children:
        html += render_unordered_list(children)

    html += "</li>"
    return html


def render_unordered_list(items: List[Dict[str, Any]]) -> str:
    """
    순서 없는 목록을 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프하고 <ul> 태그로 감싼다.
    중첩된 목록을 재귀적으로 지원한다.

    Args:
        items: 목록 항목들의 리스트

    Returns:
        HTML로 렌더링된 순서 없는 목록 ('<ul>...</ul>' 형태)
    """
    if not items:
        return "<ul></ul>"

    items_html = "".join(render_unordered_list_item(item) for item in items)
    return f"<ul>{items_html}</ul>"
