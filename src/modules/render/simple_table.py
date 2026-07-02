"""단순 테이블 렌더러."""

from typing import Dict, Any, List
from modules.render.escape import escape_html

# XSS 공격을 방지하기 위해 필터링해야 할 속성명 패턴
UNSAFE_ATTRIBUTE_PATTERNS = {
    "on",  # onclick, onload, onmouseover 등 이벤트 핸들러
}


def is_safe_attribute(attr_name: str) -> bool:
    """
    속성이 안전한지 확인한다.

    XSS 공격을 방지하기 위해 이벤트 핸들러 속성은 필터링한다.

    Args:
        attr_name: 속성명

    Returns:
        속성이 안전하면 True
    """
    attr_lower = attr_name.lower()
    for pattern in UNSAFE_ATTRIBUTE_PATTERNS:
        if attr_lower.startswith(pattern):
            return False
    return True


def escape_attribute_value(value: Any) -> str:
    """
    속성값을 안전하게 이스케이프한다.

    HTML 속성값에 포함될 수 있는 특수 문자를 이스케이프한다.

    Args:
        value: 속성값

    Returns:
        이스케이프된 속성값
    """
    return escape_html(str(value))


def render_cell_attributes(cell_attrs: Dict[str, Any]) -> str:
    """
    테이블 셀 속성을 HTML 속성 문자열로 렌더링한다.

    content 키는 제외하고, XSS 공격을 방지하기 위해 위험한 속성을 필터링한다.

    Args:
        cell_attrs: 셀 속성 딕셔너리

    Returns:
        HTML 속성 문자열 (예: 'colspan="2" rowspan="3"')
    """
    attrs = []
    for key, value in cell_attrs.items():
        # content 키는 속성이 아니라 셀 내용이므로 제외
        if key == "content":
            continue
        # 안전하지 않은 속성 필터링
        if not is_safe_attribute(key):
            continue
        # 속성값 이스케이프
        escaped_value = escape_attribute_value(value)
        attrs.append(f'{key}="{escaped_value}"')

    return " ".join(attrs)


def render_table_cell_content(cell: Any) -> str:
    """
    테이블 셀 내용을 이스케이프된 텍스트로 변환한다.

    셀은 문자열 또는 딕셔너리일 수 있다.
    속성이 있는 셀의 경우 content 키에서 텍스트를 추출한다.

    Args:
        cell: 테이블 셀 (문자열 또는 딕셔너리)

    Returns:
        이스케이프된 셀 내용
    """
    if isinstance(cell, dict):
        content = cell.get("content", "")
    else:
        content = cell

    return escape_html(str(content))


def render_simple_table_row(row: Dict[str, Any], is_header: bool = False) -> str:
    """
    테이블 행을 HTML로 렌더링한다.

    헤더 행의 경우 <th> 태그를, 데이터 행의 경우 <td> 태그를 사용한다.
    셀의 텍스트는 XSS 공격을 방지하기 위해 이스케이프되며,
    셀 속성도 안전하게 렌더링된다.

    Args:
        row: 테이블 행 딕셔너리
            - type: 'header' 또는 'data'
            - cells: 셀 내용 리스트 (문자열 또는 속성 포함 딕셔너리)
        is_header: 헤더 행 여부

    Returns:
        HTML로 렌더링된 행 ('<tr>...</tr>' 형태)
    """
    cells = row.get("cells", [])
    tag = "th" if is_header else "td"

    cell_html_list = []
    for cell in cells:
        cell_content = render_table_cell_content(cell)
        # 셀 속성을 렌더링한다 (딕셔너리인 경우만)
        attrs = ""
        if isinstance(cell, dict):
            attrs = render_cell_attributes(cell)

        # 속성이 있으면 앞에 공백을 붙인다
        if attrs:
            cell_html_list.append(f"<{tag} {attrs}>{cell_content}</{tag}>")
        else:
            cell_html_list.append(f"<{tag}>{cell_content}</{tag}>")

    cells_html = "".join(cell_html_list)
    return f"<tr>{cells_html}</tr>"


def render_simple_table(table: Dict[str, Any]) -> str:
    """
    단순 테이블을 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 셀 내용을 이스케이프하고 <table> 태그로 감싼다.
    헤더 행과 데이터 행을 구분하여 렌더링한다.

    Args:
        table: 테이블 딕셔너리
            - type: 'table'
            - rows: 행 리스트

    Returns:
        HTML로 렌더링된 테이블 ('<table>...</table>' 형태)
    """
    rows = table.get("rows", [])

    if not rows:
        return "<table></table>"

    rows_html_list = []
    for row in rows:
        row_type = row.get("type", "data")
        is_header = row_type == "header"
        rows_html_list.append(render_simple_table_row(row, is_header))

    rows_html = "".join(rows_html_list)
    return f"<table>{rows_html}</table>"
