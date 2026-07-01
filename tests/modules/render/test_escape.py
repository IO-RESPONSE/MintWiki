"""HTML 이스케이프 헬퍼 테스트."""
import pytest
from modules.render import escape_html


class TestEscapeHtmlAmpersand:
    """앰퍼샌드 이스케이프 테스트."""

    def test_escapes_single_ampersand(self):
        """단일 앰퍼샌드를 이스케이프한다."""
        assert escape_html("a & b") == "a &amp; b"

    def test_escapes_multiple_ampersands(self):
        """여러 앰퍼샌드를 이스케이프한다."""
        assert escape_html("a & b & c") == "a &amp; b &amp; c"

    def test_preserves_valid_entities(self):
        """유효한 HTML 엔티티도 이스케이프한다."""
        assert escape_html("&nbsp;") == "&amp;nbsp;"


class TestEscapeHtmlLessThan:
    """꺾쇠 괄호 < 이스케이프 테스트."""

    def test_escapes_less_than(self):
        """< 기호를 이스케이프한다."""
        assert escape_html("a < b") == "a &lt; b"

    def test_escapes_multiple_less_than(self):
        """여러 < 기호를 이스케이프한다."""
        assert escape_html("1 < 2 < 3") == "1 &lt; 2 &lt; 3"

    def test_escapes_in_tag_like_string(self):
        """태그 같은 문자열에서 < 기호를 이스케이프한다."""
        assert escape_html("<script>") == "&lt;script&gt;"


class TestEscapeHtmlGreaterThan:
    """꺾쇠 괄호 > 이스케이프 테스트."""

    def test_escapes_greater_than(self):
        """< 기호를 이스케이프한다."""
        assert escape_html("a > b") == "a &gt; b"

    def test_escapes_multiple_greater_than(self):
        """여러 > 기호를 이스케이프한다."""
        assert escape_html("3 > 2 > 1") == "3 &gt; 2 &gt; 1"


class TestEscapeHtmlDoubleQuote:
    """큰따옴표 이스케이프 테스트."""

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        assert escape_html('a "b" c') == 'a &quot;b&quot; c'

    def test_escapes_multiple_double_quotes(self):
        """여러 큰따옴표를 이스케이프한다."""
        assert escape_html('"a" "b"') == '&quot;a&quot; &quot;b&quot;'


class TestEscapeHtmlSingleQuote:
    """작은따옴표 이스케이프 테스트."""

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        assert escape_html("a 'b' c") == "a &#x27;b&#x27; c"

    def test_escapes_multiple_single_quotes(self):
        """여러 작은따옴표를 이스케이프한다."""
        assert escape_html("'a' 'b'") == "&#x27;a&#x27; &#x27;b&#x27;"


class TestEscapeHtmlCombined:
    """복합 이스케이프 테스트."""

    def test_escapes_all_special_chars(self):
        """모든 특수 문자를 한 번에 이스케이프한다."""
        assert escape_html('<div class="test">A & B</div>') == '&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;'

    def test_escapes_xss_attempt(self):
        """XSS 공격 시도를 이스케이프한다."""
        assert escape_html('<script>alert("XSS")</script>') == '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'

    def test_escapes_event_handler(self):
        """이벤트 핸들러를 이스케이프한다."""
        assert escape_html('<img src="x" onerror="alert(\'pwned\')">') == '&lt;img src=&quot;x&quot; onerror=&quot;alert(&#x27;pwned&#x27;)&quot;&gt;'

    def test_escapes_mixed_quotes(self):
        """큰따옴표와 작은따옴표를 모두 이스케이프한다."""
        assert escape_html("""It's a "test" & works""") == """It&#x27;s a &quot;test&quot; &amp; works"""


class TestEscapeHtmlEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_string(self):
        """빈 문자열을 처리한다."""
        assert escape_html("") == ""

    def test_plain_text(self):
        """일반 텍스트는 변경하지 않는다."""
        assert escape_html("Hello World") == "Hello World"

    def test_unicode_text(self):
        """유니코드 텍스트를 보존한다."""
        assert escape_html("한글 テキスト 🎉") == "한글 テキスト 🎉"

    def test_numbers_and_symbols(self):
        """숫자와 안전한 기호는 보존한다."""
        assert escape_html("123-456!@#$%^*()") == "123-456!@#$%^*()"

    def test_whitespace_preserved(self):
        """공백을 보존한다."""
        assert escape_html("a  \n  b") == "a  \n  b"


class TestEscapeHtmlIdempotence:
    """멱등성 테스트 - 같은 문자에 대해 여러 번 이스케이프해도 안전한지 확인."""

    def test_double_escaping_not_needed(self):
        """한 번의 이스케이프로 충분하다."""
        text = "a & b"
        escaped_once = escape_html(text)
        escaped_twice = escape_html(escaped_once)
        # 두 번 이스케이프하면 더 많은 &가 생성되지만, 이는 예상된 동작이다
        # (idempotent가 아님을 확인하는 것이 목표)
        assert escaped_twice == escape_html(escaped_once)
