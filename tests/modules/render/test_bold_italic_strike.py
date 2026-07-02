"""굵은, 이탤릭, 취소선 렌더러 테스트."""
import pytest
from modules.render import render_bold, render_italic, render_strike


class TestRenderBoldBasic:
    """굵은 텍스트 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트를 굵게 렌더링한다."""
        result = render_bold("bold")
        assert result == "<b>bold</b>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_bold("")
        assert result == "<b></b>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_bold("bold text here")
        assert result == "<b>bold text here</b>"

    def test_renders_single_character(self):
        """한 글자를 렌더링한다."""
        result = render_bold("a")
        assert result == "<b>a</b>"


class TestRenderBoldEscaping:
    """굵은 텍스트 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_bold("A & B")
        assert result == "<b>A &amp; B</b>"

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        result = render_bold("a < b")
        assert result == "<b>a &lt; b</b>"

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        result = render_bold("a > b")
        assert result == "<b>a &gt; b</b>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_bold('He said "hi"')
        assert result == '<b>He said &quot;hi&quot;</b>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_bold("It's a test")
        assert result == "<b>It&#x27;s a test</b>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_bold("<script>alert('xss')</script>")
        assert result == "<b>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</b>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_bold('<div class="test">A & B</div>')
        assert result == '<b>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</b>'


class TestRenderBoldUnicode:
    """굵은 텍스트 유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_bold("굵은 텍스트")
        assert result == "<b>굵은 텍스트</b>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_bold("Hello 한글 テキスト")
        assert result == "<b>Hello 한글 テキスト</b>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_bold("Test 🎉 emoji")
        assert result == "<b>Test 🎉 emoji</b>"


class TestRenderBoldWhitespace:
    """굵은 텍스트 공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_bold("a  b   c")
        assert result == "<b>a  b   c</b>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        result = render_bold("  text  ")
        assert result == "<b>  text  </b>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_bold("line1\nline2")
        assert result == "<b>line1\nline2</b>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_bold("text\twith\ttabs")
        assert result == "<b>text\twith\ttabs</b>"


class TestRenderBoldNumbers:
    """굵은 텍스트 숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        result = render_bold("123 456 789")
        assert result == "<b>123 456 789</b>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        result = render_bold("Hello! How are you?")
        assert result == "<b>Hello! How are you?</b>"

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다."""
        result = render_bold("1-2*3/4")
        assert result == "<b>1-2*3/4</b>"


class TestRenderItalicBasic:
    """이탤릭 텍스트 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트를 이탤릭으로 렌더링한다."""
        result = render_italic("italic")
        assert result == "<i>italic</i>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_italic("")
        assert result == "<i></i>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_italic("italic text here")
        assert result == "<i>italic text here</i>"

    def test_renders_single_character(self):
        """한 글자를 렌더링한다."""
        result = render_italic("a")
        assert result == "<i>a</i>"


class TestRenderItalicEscaping:
    """이탤릭 텍스트 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_italic("A & B")
        assert result == "<i>A &amp; B</i>"

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        result = render_italic("a < b")
        assert result == "<i>a &lt; b</i>"

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        result = render_italic("a > b")
        assert result == "<i>a &gt; b</i>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_italic('He said "hi"')
        assert result == '<i>He said &quot;hi&quot;</i>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_italic("It's a test")
        assert result == "<i>It&#x27;s a test</i>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_italic("<script>alert('xss')</script>")
        assert result == "<i>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</i>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_italic('<div class="test">A & B</div>')
        assert result == '<i>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</i>'


class TestRenderItalicUnicode:
    """이탤릭 텍스트 유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_italic("이탤릭 텍스트")
        assert result == "<i>이탤릭 텍스트</i>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_italic("Hello 한글 テキスト")
        assert result == "<i>Hello 한글 テキスト</i>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_italic("Test 🎉 emoji")
        assert result == "<i>Test 🎉 emoji</i>"


class TestRenderItalicWhitespace:
    """이탤릭 텍스트 공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_italic("a  b   c")
        assert result == "<i>a  b   c</i>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        result = render_italic("  text  ")
        assert result == "<i>  text  </i>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_italic("line1\nline2")
        assert result == "<i>line1\nline2</i>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_italic("text\twith\ttabs")
        assert result == "<i>text\twith\ttabs</i>"


class TestRenderItalicNumbers:
    """이탤릭 텍스트 숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        result = render_italic("123 456 789")
        assert result == "<i>123 456 789</i>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        result = render_italic("Hello! How are you?")
        assert result == "<i>Hello! How are you?</i>"

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다."""
        result = render_italic("1-2*3/4")
        assert result == "<i>1-2*3/4</i>"


class TestRenderStrikeBasic:
    """취소선 텍스트 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트에 취소선을 렌더링한다."""
        result = render_strike("strike")
        assert result == "<s>strike</s>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_strike("")
        assert result == "<s></s>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_strike("strike text here")
        assert result == "<s>strike text here</s>"

    def test_renders_single_character(self):
        """한 글자를 렌더링한다."""
        result = render_strike("a")
        assert result == "<s>a</s>"


class TestRenderStrikeEscaping:
    """취소선 텍스트 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_strike("A & B")
        assert result == "<s>A &amp; B</s>"

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        result = render_strike("a < b")
        assert result == "<s>a &lt; b</s>"

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        result = render_strike("a > b")
        assert result == "<s>a &gt; b</s>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_strike('He said "hi"')
        assert result == '<s>He said &quot;hi&quot;</s>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_strike("It's a test")
        assert result == "<s>It&#x27;s a test</s>"

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_strike("<script>alert('xss')</script>")
        assert result == "<s>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</s>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_strike('<div class="test">A & B</div>')
        assert result == '<s>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</s>'


class TestRenderStrikeUnicode:
    """취소선 텍스트 유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_strike("취소선 텍스트")
        assert result == "<s>취소선 텍스트</s>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_strike("Hello 한글 テキスト")
        assert result == "<s>Hello 한글 テキスト</s>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_strike("Test 🎉 emoji")
        assert result == "<s>Test 🎉 emoji</s>"


class TestRenderStrikeWhitespace:
    """취소선 텍스트 공백 처리 테스트."""

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_strike("a  b   c")
        assert result == "<s>a  b   c</s>"

    def test_preserves_leading_and_trailing_spaces(self):
        """앞뒤 공백을 보존한다."""
        result = render_strike("  text  ")
        assert result == "<s>  text  </s>"

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_strike("line1\nline2")
        assert result == "<s>line1\nline2</s>"

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_strike("text\twith\ttabs")
        assert result == "<s>text\twith\ttabs</s>"


class TestRenderStrikeNumbers:
    """취소선 텍스트 숫자 및 기호 테스트."""

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        result = render_strike("123 456 789")
        assert result == "<s>123 456 789</s>"

    def test_preserves_safe_punctuation(self):
        """안전한 구두점을 보존한다."""
        result = render_strike("Hello! How are you?")
        assert result == "<s>Hello! How are you?</s>"

    def test_preserves_mathematical_symbols(self):
        """수학 기호를 보존한다."""
        result = render_strike("1-2*3/4")
        assert result == "<s>1-2*3/4</s>"
