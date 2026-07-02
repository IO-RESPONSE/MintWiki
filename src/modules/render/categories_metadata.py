"""카테고리 메타데이터 렌더러."""

from typing import List
from modules.render.escape import escape_html


def render_categories_metadata(categories: List[str]) -> str:
    """
    카테고리 메타데이터를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 각 카테고리명을 이스케이프하여 링크로 감싼다.
    카테고리명은 사용자 입력으로 취급하여 안전하게 처리한다.

    Args:
        categories: 카테고리명 리스트

    Returns:
        HTML로 렌더링된 카테고리 메타데이터 (카테고리 링크들 포함)
    """
    if not categories:
        return '<div class="categories-metadata"></div>'

    # 각 카테고리를 링크로 렌더링
    category_links = []
    for category in categories:
        escaped_category = escape_html(category)
        # 카테고리 링크의 href는 /wiki/Category:카테고리명 형태
        href = f"/wiki/Category:{escaped_category}"
        category_links.append(f'<a href="{href}">{escaped_category}</a>')

    # 카테고리 링크들을 쉼표로 구분하여 div에 담기
    categories_html = ", ".join(category_links)
    return f'<div class="categories-metadata">{categories_html}</div>'
