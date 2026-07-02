"""단순 테이블 렌더러 테스트."""
import pytest
from modules.render import render_simple_table


class TestRenderSimpleTableBasic:
    """단순 테이블 렌더링 기본 테스트."""

    def test_renders_empty_table(self):
        """빈 테이블을 렌더링한다."""
        table = {"type": "table", "rows": []}
        result = render_simple_table(table)
        assert result == "<table></table>"

    def test_renders_single_cell(self):
        """단일 셀을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["cell1"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>cell1</td></tr></table>"

    def test_renders_single_row_multiple_cells(self):
        """한 행에 여러 셀을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["cell1", "cell2", "cell3"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>cell1</td><td>cell2</td><td>cell3</td></tr></table>"

    def test_renders_multiple_rows(self):
        """여러 행을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {"type": "data", "cells": ["row1col1", "row1col2"]},
                {"type": "data", "cells": ["row2col1", "row2col2"]},
                {"type": "data", "cells": ["row3col1", "row3col2"]},
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><td>row1col1</td><td>row1col2</td></tr><tr><td>row2col1</td><td>row2col2</td></tr><tr><td>row3col1</td><td>row3col2</td></tr></table>"
        )

    def test_renders_empty_cells(self):
        """빈 셀을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["", "cell2", ""]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td></td><td>cell2</td><td></td></tr></table>"


class TestRenderSimpleTableEscaping:
    """단순 테이블 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["A & B"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>A &amp; B</td></tr></table>"

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["a < b"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>a &lt; b</td></tr></table>"

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["a > b"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>a &gt; b</td></tr></table>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ['He said "hi"']}],
        }
        result = render_simple_table(table)
        assert result == '<table><tr><td>He said &quot;hi&quot;</td></tr></table>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["It's a test"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>It&#x27;s a test</td></tr></table>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["<script>alert('xss')</script>"]}],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><td>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</td></tr></table>"
        )

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [
                {"type": "data", "cells": ['<div class="test">A & B</div>']}
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == '<table><tr><td>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</td></tr></table>'
        )

    def test_escapes_multiple_cells_with_special_chars(self):
        """여러 셀의 특수 문자를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [
                {"type": "data", "cells": ["A & B", "<tag>", 'quote"test']}
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == '<table><tr><td>A &amp; B</td><td>&lt;tag&gt;</td><td>quote&quot;test</td></tr></table>'
        )


class TestRenderSimpleTableHeaderRows:
    """단순 테이블 헤더 행 테스트."""

    def test_renders_header_row(self):
        """헤더 행을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [{"type": "header", "cells": ["Header1", "Header2"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><th>Header1</th><th>Header2</th></tr></table>"

    def test_renders_header_with_data_rows(self):
        """헤더 행과 데이터 행을 함께 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {"type": "header", "cells": ["Name", "Age"]},
                {"type": "data", "cells": ["Alice", "30"]},
                {"type": "data", "cells": ["Bob", "25"]},
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><th>Name</th><th>Age</th></tr><tr><td>Alice</td><td>30</td></tr><tr><td>Bob</td><td>25</td></tr></table>"
        )

    def test_escapes_header_cells(self):
        """헤더 셀의 특수 문자를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [{"type": "header", "cells": ["<script>alert('xss')</script>"]}],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><th>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</th></tr></table>"
        )

    def test_renders_multiple_header_rows(self):
        """여러 헤더 행을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {"type": "header", "cells": ["Header1", "Header2"]},
                {"type": "header", "cells": ["Subheader1", "Subheader2"]},
                {"type": "data", "cells": ["data1", "data2"]},
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><th>Header1</th><th>Header2</th></tr><tr><th>Subheader1</th><th>Subheader2</th></tr><tr><td>data1</td><td>data2</td></tr></table>"
        )


class TestRenderSimpleTableUnicode:
    """단순 테이블 유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["한글 셀", "테이블"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>한글 셀</td><td>테이블</td></tr></table>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": ["Hello 한글 テキスト", "Mixed language test"],
                }
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><td>Hello 한글 テキスト</td><td>Mixed language test</td></tr></table>"
        )

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["Test 🎉 emoji", "More 🚀 emojis"]}],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><td>Test 🎉 emoji</td><td>More 🚀 emojis</td></tr></table>"
        )


class TestRenderSimpleTableWhitespace:
    """단순 테이블 공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["a  b   c"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>a  b   c</td></tr></table>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["  text  "]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>  text  </td></tr></table>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["line1\nline2"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>line1\nline2</td></tr></table>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["text\twith\ttabs"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>text\twith\ttabs</td></tr></table>"


class TestRenderSimpleTableNumbers:
    """단순 테이블 숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["123", "456", "789"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>123</td><td>456</td><td>789</td></tr></table>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["Hello! How are you?"]}],
        }
        result = render_simple_table(table)
        assert (
            result == "<table><tr><td>Hello! How are you?</td></tr></table>"
        )

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["1-2*3/4"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>1-2*3/4</td></tr></table>"


class TestRenderSimpleTableCellTypes:
    """단순 테이블 셀 유형 테스트."""

    def test_handles_string_cells(self):
        """문자열 셀을 처리한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": ["string1", "string2"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>string1</td><td>string2</td></tr></table>"

    def test_handles_dict_cells_with_content(self):
        """content 키를 가진 딕셔너리 셀을 처리한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "cell1"},
                        {"content": "cell2"},
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>cell1</td><td>cell2</td></tr></table>"

    def test_handles_dict_cells_without_content_key(self):
        """content 키가 없는 딕셔너리 셀을 처리한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": [{"colspan": 2}, {"rowspan": 3}]}],
        }
        result = render_simple_table(table)
        assert result == '<table><tr><td colspan="2"></td><td rowspan="3"></td></tr></table>'

    def test_handles_mixed_cell_types(self):
        """문자열과 딕셔너리 셀을 혼합하여 처리한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        "string_cell",
                        {"content": "dict_cell"},
                        "another_string",
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == "<table><tr><td>string_cell</td><td>dict_cell</td><td>another_string</td></tr></table>"
        )


class TestRenderSimpleTableCellAttributes:
    """단순 테이블 셀 속성 렌더링 테스트."""

    def test_renders_colspan_attribute(self):
        """colspan 속성을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "Merged", "colspan": 2},
                        "Normal",
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == '<table><tr><td colspan="2">Merged</td><td>Normal</td></tr></table>'
        )

    def test_renders_rowspan_attribute(self):
        """rowspan 속성을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "Span 2", "rowspan": 2},
                        "Col 2",
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert (
            result
            == '<table><tr><td rowspan="2">Span 2</td><td>Col 2</td></tr></table>'
        )

    def test_renders_multiple_attributes(self):
        """여러 속성을 함께 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "Merged", "colspan": 2, "rowspan": 3}
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        # colspan과 rowspan이 모두 포함되어야 함
        assert "colspan=" in result
        assert "rowspan=" in result
        assert "Merged" in result

    def test_escapes_attribute_values(self):
        """속성값의 특수 문자를 이스케이프한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "Cell", "class": 'test"value'}
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        # 큰따옴표가 이스케이프되어야 함
        assert "&quot;" in result
        assert 'class="test&quot;value"' in result

    def test_filters_onclick_attribute(self):
        """onclick 속성을 필터링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "onclick": "alert('xss')",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        # onclick이 렌더링되지 않아야 함
        assert "onclick" not in result
        assert "<td>Cell</td>" in result

    def test_filters_onload_attribute(self):
        """onload 속성을 필터링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "onload": "malicious()",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert "onload" not in result
        assert "<td>Cell</td>" in result

    def test_filters_onerror_attribute(self):
        """onerror 속성을 필터링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "onerror": "attack()",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert "onerror" not in result
        assert "<td>Cell</td>" in result

    def test_renders_safe_custom_attributes(self):
        """안전한 커스텀 속성을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "data-id": "12345",
                            "data-type": "special",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert 'data-id="12345"' in result
        assert 'data-type="special"' in result
        assert "Cell" in result

    def test_renders_class_attribute(self):
        """class 속성을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "class": "highlight bold",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert 'class="highlight bold"' in result

    def test_renders_id_attribute(self):
        """id 속성을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "id": "cell-123",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert 'id="cell-123"' in result

    def test_renders_header_cells_with_attributes(self):
        """속성이 있는 헤더 셀을 렌더링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "header",
                    "cells": [
                        {
                            "content": "Header",
                            "colspan": 2,
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert '<th colspan="2">Header</th>' in result

    def test_handles_numeric_attribute_values(self):
        """숫자 속성값을 처리한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "colspan": 3,
                            "rowspan": 2,
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert 'colspan="3"' in result
        assert 'rowspan="2"' in result

    def test_event_handler_with_uppercase_is_filtered(self):
        """대문자 이벤트 핸들러도 필터링한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "ONCLICK": "alert('xss')",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        assert "ONCLICK" not in result and "onclick" not in result
        assert "<td>Cell</td>" in result

    def test_mixed_safe_and_unsafe_attributes(self):
        """안전한 속성과 위험한 속성이 섞여 있을 때 처리한다."""
        table = {
            "type": "table",
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {
                            "content": "Cell",
                            "colspan": 2,
                            "onclick": "alert('xss')",
                            "class": "safe",
                        }
                    ],
                }
            ],
        }
        result = render_simple_table(table)
        # 안전한 속성은 포함
        assert 'colspan="2"' in result
        assert 'class="safe"' in result
        # 위험한 속성은 제외
        assert "onclick" not in result


class TestRenderSimpleTableEdgeCases:
    """단순 테이블 엣지 케이스 테스트."""

    def test_handles_numeric_cell_content(self):
        """숫자 셀 내용을 처리한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": [123, 456.78, 0]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>123</td><td>456.78</td><td>0</td></tr></table>"

    def test_handles_long_cell_text(self):
        """긴 셀 텍스트를 처리한다."""
        long_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 5
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": [long_text]}],
        }
        result = render_simple_table(table)
        assert result.startswith("<table><tr><td>")
        assert result.endswith("</td></tr></table>")
        assert long_text in result

    def test_handles_many_columns(self):
        """많은 열을 처리한다."""
        cells = [f"col{i}" for i in range(100)]
        table = {
            "type": "table",
            "rows": [{"type": "data", "cells": cells}],
        }
        result = render_simple_table(table)
        assert result.startswith("<table><tr>")
        assert result.endswith("</tr></table>")
        assert "col0" in result
        assert "col99" in result

    def test_handles_many_rows(self):
        """많은 행을 처리한다."""
        rows = [
            {"type": "data", "cells": [f"row{i}col1", f"row{i}col2"]}
            for i in range(100)
        ]
        table = {"type": "table", "rows": rows}
        result = render_simple_table(table)
        assert result.startswith("<table>")
        assert result.endswith("</table>")
        assert "row0col1" in result
        assert "row99col1" in result

    def test_handles_missing_rows_key(self):
        """rows 키가 없는 테이블을 처리한다."""
        table = {"type": "table"}
        result = render_simple_table(table)
        assert result == "<table></table>"

    def test_handles_missing_cells_key_in_row(self):
        """행에서 cells 키가 없는 경우를 처리한다."""
        table = {
            "type": "table",
            "rows": [{"type": "data"}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr></tr></table>"

    def test_handles_default_row_type_as_data(self):
        """기본 행 타입을 data로 처리한다."""
        table = {
            "type": "table",
            "rows": [{"cells": ["cell1", "cell2"]}],
        }
        result = render_simple_table(table)
        assert result == "<table><tr><td>cell1</td><td>cell2</td></tr></table>"
