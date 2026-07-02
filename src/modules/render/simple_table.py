"""단순 테이블 렌더러."""

from typing import Dict, Any, List
from modules.render.escape import escape_html


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
    셀의 텍스트는 XSS 공격을 방지하기 위해 이스케이프된다.

    Args:
        row: 테이블 행 딕셔너리
            - type: 'header' 또는 'data'
            - cells: 셀 내용 리스트
        is_header: 헤더 행 여부

    Returns:
        HTML로 렌더링된 행 ('<tr>...</tr>' 형태)
    """
    cells = row.get("cells", [])
    tag = "th" if is_header else "td"

    cell_html_list = []
    for cell in cells:
        cell_content = render_table_cell_content(cell)
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
