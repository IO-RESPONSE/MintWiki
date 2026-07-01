"""평문 문단 렌더러 테스트."""
import pytest
from modules.render import render_plain_paragraph


class TestRenderPlainParagraphBasic:
    """평문 문단 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트를 렌더링한다."""
        result = render_plain_paragraph("Hello, World!")
        assert result == "<p>Hello, World!</p>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_plain_paragraph("")
        assert result == "<p></p>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_plain_paragraph("This is a test")
        assert result == "<p>This is a test</p>"


class TestRenderPlainParagraphEscaping:
    """HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_plain_paragraph("A & B")
        assert result == "<p>A &amp; B</p>"

    def test_escapes_less_than(self):
        """꺾쇠괄호 <를 이스케이프한다."""
        result = render_plain_paragraph("a < b")
        assert result == "<p>a &lt; b</p>"

    def test_escapes_greater_than(self):
        """꺾쇠괄호 >를 이스케이프한다."""
        result = render_plain_paragraph("a > b")
        assert result == "<p>a &gt; b</p>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_plain_paragraph('He said "hi"')
        assert result == '<p>He said &quot;hi&quot;</p>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_plain_paragraph("It's a test")
        assert result == "<p>It&#x27;s a test</p>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_plain_paragraph("<script>alert('xss')</script>")
        assert result == "<p>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</p>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_plain_paragraph('<div class="test">A & B</div>')
        assert result == '<p>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</p>'


class TestRenderPlainParagraphUnicode:
    """유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_plain_paragraph("이것은 테스트입니다")
        assert result == "<p>이것은 테스트입니다</p>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_plain_paragraph("Hello 한글 テキスト")
        assert result == "<p>Hello 한글 テキスト</p>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_plain_paragraph("Test 🎉 emoji")
        assert result == "<p>Test 🎉 emoji</p>"


class TestRenderPlainParagraphWhitespace:
    """공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_plain_paragraph("a  b   c")
        assert result == "<p>a  b   c</p>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        result = render_plain_paragraph("  text  ")
        assert result == "<p>  text  </p>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_plain_paragraph("line1\nline2")
        assert result == "<p>line1\nline2</p>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_plain_paragraph("text\twith\ttabs")
        assert result == "<p>text\twith\ttabs</p>"


class TestRenderPlainParagraphNumbers:
    """숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        result = render_plain_paragraph("123 456 789")
        assert result == "<p>123 456 789</p>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        result = render_plain_paragraph("Hello! How are you?")
        assert result == "<p>Hello! How are you?</p>"

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다 (-, *, /)."""
        result = render_plain_paragraph("1-2*3/4")
        assert result == "<p>1-2*3/4</p>"


class TestRenderPlainParagraphLongText:
    """긴 텍스트 테스트."""

    def test_renders_long_paragraph(self):
        """긴 문단을 렌더링한다."""
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " * 5
        result = render_plain_paragraph(text)
        assert result.startswith("<p>")
        assert result.endswith("</p>")
        assert text in result

    def test_renders_paragraph_with_special_chars_in_long_text(self):
        """특수 문자가 있는 긴 문단을 렌더링한다."""
        text = "Test & test < test > test ' test \" test " * 3
        result = render_plain_paragraph(text)
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&#x27;" in result
        assert "&quot;" in result
