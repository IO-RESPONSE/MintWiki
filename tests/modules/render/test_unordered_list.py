"""순서 없는 목록 렌더러 테스트."""
import pytest
from modules.render import render_unordered_list


class TestRenderUnorderedListBasic:
    """순서 없는 목록 렌더링 기본 테스트."""

    def test_renders_empty_list(self):
        """빈 목록을 렌더링한다."""
        result = render_unordered_list([])
        assert result == "<ul></ul>"

    def test_renders_single_item(self):
        """단일 항목을 렌더링한다."""
        items = [{"level": 1, "text": "Item 1", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Item 1</li></ul>"

    def test_renders_two_items(self):
        """두 개의 항목을 렌더링한다."""
        items = [
            {"level": 1, "text": "Item 1", "children": []},
            {"level": 1, "text": "Item 2", "children": []},
        ]
        result = render_unordered_list(items)
        assert result == "<ul><li>Item 1</li><li>Item 2</li></ul>"

    def test_renders_multiple_items(self):
        """여러 항목을 렌더링한다."""
        items = [
            {"level": 1, "text": "First item", "children": []},
            {"level": 1, "text": "Second item", "children": []},
            {"level": 1, "text": "Third item", "children": []},
        ]
        result = render_unordered_list(items)
        assert result == "<ul><li>First item</li><li>Second item</li><li>Third item</li></ul>"


class TestRenderUnorderedListEscaping:
    """순서 없는 목록 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        items = [{"level": 1, "text": "A & B", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>A &amp; B</li></ul>"

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        items = [{"level": 1, "text": "a < b", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>a &lt; b</li></ul>"

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        items = [{"level": 1, "text": "a > b", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>a &gt; b</li></ul>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        items = [{"level": 1, "text": 'He said "hi"', "children": []}]
        result = render_unordered_list(items)
        assert result == '<ul><li>He said &quot;hi&quot;</li></ul>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        items = [{"level": 1, "text": "It's a test", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>It&#x27;s a test</li></ul>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        items = [{"level": 1, "text": "<script>alert('xss')</script>", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</li></ul>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        items = [{"level": 1, "text": '<div class="test">A & B</div>', "children": []}]
        result = render_unordered_list(items)
        assert result == '<ul><li>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</li></ul>'


class TestRenderUnorderedListUnicode:
    """순서 없는 목록 유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        items = [{"level": 1, "text": "한글 항목", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>한글 항목</li></ul>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        items = [{"level": 1, "text": "Hello 한글 テキスト", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Hello 한글 テキスト</li></ul>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        items = [{"level": 1, "text": "Test 🎉 emoji", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Test 🎉 emoji</li></ul>"


class TestRenderUnorderedListWhitespace:
    """순서 없는 목록 공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        items = [{"level": 1, "text": "a  b   c", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>a  b   c</li></ul>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        items = [{"level": 1, "text": "  text  ", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>  text  </li></ul>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        items = [{"level": 1, "text": "line1\nline2", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>line1\nline2</li></ul>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        items = [{"level": 1, "text": "text\twith\ttabs", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>text\twith\ttabs</li></ul>"


class TestRenderUnorderedListNumbers:
    """순서 없는 목록 숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        items = [{"level": 1, "text": "123 456 789", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>123 456 789</li></ul>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        items = [{"level": 1, "text": "Hello! How are you?", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Hello! How are you?</li></ul>"

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다."""
        items = [{"level": 1, "text": "1-2*3/4", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>1-2*3/4</li></ul>"


class TestRenderUnorderedListNested:
    """순서 없는 목록 중첩 테스트."""

    def test_renders_single_level_nested(self):
        """단일 단계의 중첩 목록을 렌더링한다."""
        items = [
            {
                "level": 1,
                "text": "Item 1",
                "children": [
                    {"level": 2, "text": "Nested 1.1", "children": []},
                    {"level": 2, "text": "Nested 1.2", "children": []},
                ],
            },
        ]
        result = render_unordered_list(items)
        assert (
            result
            == "<ul><li>Item 1<ul><li>Nested 1.1</li><li>Nested 1.2</li></ul></li></ul>"
        )

    def test_renders_multiple_items_with_nested(self):
        """여러 항목 중 일부가 중첩된 목록을 렌더링한다."""
        items = [
            {
                "level": 1,
                "text": "Item 1",
                "children": [
                    {"level": 2, "text": "Nested 1.1", "children": []},
                ],
            },
            {"level": 1, "text": "Item 2", "children": []},
        ]
        result = render_unordered_list(items)
        assert (
            result
            == "<ul><li>Item 1<ul><li>Nested 1.1</li></ul></li><li>Item 2</li></ul>"
        )

    def test_renders_deep_nested(self):
        """깊게 중첩된 목록을 렌더링한다."""
        items = [
            {
                "level": 1,
                "text": "Item 1",
                "children": [
                    {
                        "level": 2,
                        "text": "Nested 1.1",
                        "children": [
                            {"level": 3, "text": "Deep 1.1.1", "children": []},
                        ],
                    },
                ],
            },
        ]
        result = render_unordered_list(items)
        assert (
            result
            == "<ul><li>Item 1<ul><li>Nested 1.1<ul><li>Deep 1.1.1</li></ul></li></ul></li></ul>"
        )

    def test_renders_nested_with_special_chars(self):
        """중첩된 목록에서 특수 문자를 이스케이프한다."""
        items = [
            {
                "level": 1,
                "text": "Item with & special",
                "children": [
                    {"level": 2, "text": "<nested>", "children": []},
                ],
            },
        ]
        result = render_unordered_list(items)
        assert (
            result
            == "<ul><li>Item with &amp; special<ul><li>&lt;nested&gt;</li></ul></li></ul>"
        )


class TestRenderUnorderedListEdgeCases:
    """순서 없는 목록 엣지 케이스 테스트."""

    def test_handles_empty_text(self):
        """빈 텍스트를 가진 항목을 렌더링한다."""
        items = [{"level": 1, "text": "", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li></li></ul>"

    def test_handles_missing_children_key(self):
        """children 키가 없는 항목을 처리한다."""
        items = [{"level": 1, "text": "Item"}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Item</li></ul>"

    def test_handles_empty_children(self):
        """빈 children 리스트를 처리한다."""
        items = [{"level": 1, "text": "Item", "children": []}]
        result = render_unordered_list(items)
        assert result == "<ul><li>Item</li></ul>"

    def test_handles_long_item_text(self):
        """긴 항목 텍스트를 렌더링한다."""
        long_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
        items = [{"level": 1, "text": long_text, "children": []}]
        result = render_unordered_list(items)
        assert result.startswith("<ul><li>")
        assert result.endswith("</li></ul>")
        assert long_text in result

    def test_handles_many_items(self):
        """많은 항목을 렌더링한다."""
        items = [
            {"level": 1, "text": f"Item {i}", "children": []}
            for i in range(100)
        ]
        result = render_unordered_list(items)
        assert result.startswith("<ul>")
        assert result.endswith("</ul>")
        assert "Item 0" in result
        assert "Item 99" in result
