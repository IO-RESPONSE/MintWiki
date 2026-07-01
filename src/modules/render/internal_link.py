"""내부 링크 렌더러."""

from typing import Optional
from modules.render.escape import escape_html


def render_internal_link(page: str, label: Optional[str] = None) -> str:
    """
    내부 링크를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 페이지명과 레이블을 이스케이프한 후 <a> 태그로 감싼다.
    페이지명과 레이블 모두 사용자 입력으로 취급하여 안전하게 처리한다.

    Args:
        page: 링크할 페이지명
        label: 링크 텍스트 (생략하면 페이지명 사용)

    Returns:
        HTML로 렌더링된 내부 링크 ('<a href="...">...</a>' 형태)
    """
    # 페이지명으로부터 안전한 href 생성
    # 페이지명 자체는 이스케이프하지 않고, 슬래시와 쿼리 문자는 인코딩하여 보존
    escaped_page = escape_html(page)

    # href는 URL 경로이므로, 페이지명의 특수 문자는 그대로 두고 문제가 될 HTML은 방지
    # 하지만 href 속성 내에서 특수 문자가 속성을 깨뜨리지 않도록 이스케이프
    href = f"/wiki/{escaped_page}"

    # 레이블 설정: 레이블이 없으면 페이지명 사용
    display_text = label if label is not None else page
    escaped_label = escape_html(display_text)

    return f'<a href="{href}">{escaped_label}</a>'
