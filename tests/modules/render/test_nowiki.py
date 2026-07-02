"""nowiki 렌더러 테스트."""
import pytest
from modules.render import render_nowiki


class TestRenderNowikiBasic:
    """nowiki 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트를 렌더링한다."""
        result = render_nowiki("Hello, World!")
        assert result == "<code>Hello, World!</code>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_nowiki("")
        assert result == "<code></code>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_nowiki("text with spaces")
        assert result == "<code>text with spaces</code>"


class TestRenderNowikiWikiMarkup:
    """위키 마크업 처리 테스트."""

    def test_preserves_bold_markup(self):
        """굵은 마크업을 그대로 보존한다."""
        result = render_nowiki("'''bold'''")
        assert result == "<code>&#x27;&#x27;&#x27;bold&#x27;&#x27;&#x27;</code>"

    def test_preserves_italic_markup(self):
        """이탤릭 마크업을 그대로 보존한다."""
        result = render_nowiki("''italic''")
        assert result == "<code>&#x27;&#x27;italic&#x27;&#x27;</code>"

    def test_preserves_link_markup(self):
        """링크 마크업을 그대로 보존한다."""
        result = render_nowiki("[[Link]]")
        assert result == "<code>[[Link]]</code>"

    def test_preserves_multiple_wiki_markup(self):
        """여러 위키 마크업을 보존한다."""
        result = render_nowiki("[[Link]] and '''bold''' and ''italic''")
        assert result == "<code>[[Link]] and &#x27;&#x27;&#x27;bold&#x27;&#x27;&#x27; and &#x27;&#x27;italic&#x27;&#x27;</code>"

    def test_preserves_list_markup(self):
        """목록 마크업을 그대로 보존한다."""
        result = render_nowiki("* Item 1\n* Item 2")
        assert result == "<code>* Item 1\n* Item 2</code>"

    def test_preserves_heading_markup(self):
        """제목 마크업을 그대로 보존한다."""
        result = render_nowiki("= Heading =")
        assert result == "<code>= Heading =</code>"


class TestRenderNowikiHtmlEscaping:
    """HTML 이스케이프 테스트."""

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_nowiki("<script>alert('xss')</script>")
        assert result == "<code>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</code>"

    def test_escapes_less_than(self):
        """< 기호를 이스케이프한다."""
        result = render_nowiki("a < b")
        assert result == "<code>a &lt; b</code>"

    def test_escapes_greater_than(self):
        """> 기호를 이스케이프한다."""
        result = render_nowiki("a > b")
        assert result == "<code>a &gt; b</code>"

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_nowiki("a & b")
        assert result == "<code>a &amp; b</code>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_nowiki('He said "hi"')
        assert result == '<code>He said &quot;hi&quot;</code>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_nowiki("It's a test")
        assert result == "<code>It&#x27;s a test</code>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_nowiki('<div class="test">A & B</div>')
        assert result == '<code>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</code>'


class TestRenderNowikiSpecialCharacters:
    """특수 문자 처리 테스트."""

    def test_preserves_math_symbols(self):
        """수학 기호를 보존한다."""
        result = render_nowiki("1 + 2 = 3")
        assert result == "<code>1 + 2 = 3</code>"

    def test_preserves_punctuation(self):
        """구두점을 보존한다."""
        result = render_nowiki("Hello! How are you?")
        assert result == "<code>Hello! How are you?</code>"

    def test_preserves_special_wiki_chars(self):
        """특수 위키 문자를 보존한다."""
        result = render_nowiki("< > & ' \" [[ ]] {{ }}")
        assert result == "<code>&lt; &gt; &amp; &#x27; &quot; [[ ]] {{ }}</code>"


class TestRenderNowikiMultiline:
    """여러 줄 콘텐츠 테스트."""

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_nowiki("line1\nline2\nline3")
        assert result == "<code>line1\nline2\nline3</code>"

    def test_preserves_blank_lines(self):
        """빈 줄을 보존한다."""
        result = render_nowiki("line1\n\nline2")
        assert result == "<code>line1\n\nline2</code>"

    def test_preserves_leading_trailing_whitespace(self):
        """앞뒤 공백을 보존한다."""
        result = render_nowiki("  text  ")
        assert result == "<code>  text  </code>"

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_nowiki("a  b   c")
        assert result == "<code>a  b   c</code>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_nowiki("text\twith\ttabs")
        assert result == "<code>text\twith\ttabs</code>"


class TestRenderNowikiUnicode:
    """유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_nowiki("이것은 테스트입니다")
        assert result == "<code>이것은 테스트입니다</code>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_nowiki("Hello 한글 テキスト")
        assert result == "<code>Hello 한글 テキスト</code>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_nowiki("Test 🎉 emoji 🚀")
        assert result == "<code>Test 🎉 emoji 🚀</code>"


class TestRenderNowikiComplexContent:
    """복잡한 콘텐츠 테스트."""

    def test_renders_code_example(self):
        """코드 예제를 렌더링한다."""
        code = 'def hello(name):\n    print(f"Hello {name}")'
        result = render_nowiki(code)
        assert "def hello(name):" in result
        assert 'f&quot;Hello {name}&quot;' in result

    def test_renders_html_entity_references(self):
        """HTML 엔티티 참조를 이스케이프한다."""
        result = render_nowiki("&lt;tag&gt; and &amp;")
        assert result == "<code>&amp;lt;tag&amp;gt; and &amp;amp;</code>"

    def test_renders_wiki_with_html_escapes(self):
        """위키 마크업과 HTML 특수문자를 함께 처리한다."""
        result = render_nowiki("[[Link]] < [[Other]]")
        assert result == "<code>[[Link]] &lt; [[Other]]</code>"


class TestRenderNowikiEdgeCases:
    """엣지 케이스 테스트."""

    def test_renders_only_whitespace(self):
        """공백만 있는 콘텐츠를 렌더링한다."""
        result = render_nowiki("   \n\t  ")
        assert result == "<code>   \n\t  </code>"

    def test_renders_single_character(self):
        """단일 문자를 렌더링한다."""
        result = render_nowiki("a")
        assert result == "<code>a</code>"

    def test_renders_long_content(self):
        """긴 콘텐츠를 렌더링한다."""
        text = "Lorem ipsum dolor sit amet, " * 100
        result = render_nowiki(text)
        assert result.startswith("<code>")
        assert result.endswith("</code>")
        assert text in result

    def test_renders_all_special_chars_combined(self):
        """모든 특수 문자를 함께 렌더링한다."""
        result = render_nowiki("< > & \" ' [[ ]] '''bold''' ''italic'' [[Link]]")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
        assert "&#x27;" in result
        assert "[[" in result
        assert "]]" in result
