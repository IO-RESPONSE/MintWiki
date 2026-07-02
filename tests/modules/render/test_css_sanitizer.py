"""CSS 값 새니타이저 테스트."""
import pytest
from modules.render import sanitize_css_value


class TestSanitizeCssValueSafeValues:
    """안전한 CSS 값 테스트."""

    def test_allows_simple_color(self):
        """단순 색상 값을 허용한다."""
        assert sanitize_css_value("red") == "red"
        assert sanitize_css_value("#FF0000") == "#FF0000"
        assert sanitize_css_value("rgb(255, 0, 0)") == "rgb(255, 0, 0)"

    def test_allows_simple_dimensions(self):
        """단순 차원 값을 허용한다."""
        assert sanitize_css_value("10px") == "10px"
        assert sanitize_css_value("50%") == "50%"
        assert sanitize_css_value("2em") == "2em"
        assert sanitize_css_value("auto") == "auto"

    def test_allows_padding_and_margin(self):
        """padding과 margin 값을 허용한다."""
        assert sanitize_css_value("10px 20px") == "10px 20px"
        assert sanitize_css_value("5px") == "5px"
        assert sanitize_css_value("10px 20px 30px 40px") == "10px 20px 30px 40px"

    def test_allows_text_alignment(self):
        """텍스트 정렬 값을 허용한다."""
        assert sanitize_css_value("left") == "left"
        assert sanitize_css_value("center") == "center"
        assert sanitize_css_value("right") == "right"
        assert sanitize_css_value("justify") == "justify"

    def test_allows_font_properties(self):
        """폰트 속성을 허용한다."""
        assert sanitize_css_value("Arial, sans-serif") == "Arial, sans-serif"
        assert sanitize_css_value("bold") == "bold"
        assert sanitize_css_value("italic") == "italic"
        assert sanitize_css_value("14px") == "14px"

    def test_allows_border_properties(self):
        """border 속성을 허용한다."""
        assert sanitize_css_value("1px solid black") == "1px solid black"
        assert sanitize_css_value("none") == "none"
        assert sanitize_css_value("2px dashed #333") == "2px dashed #333"

    def test_allows_background_color(self):
        """background 색상을 허용한다."""
        assert sanitize_css_value("white") == "white"
        assert sanitize_css_value("#f0f0f0") == "#f0f0f0"
        assert sanitize_css_value("rgba(0, 0, 0, 0.5)") == "rgba(0, 0, 0, 0.5)"

    def test_allows_display_values(self):
        """display 값을 허용한다."""
        assert sanitize_css_value("block") == "block"
        assert sanitize_css_value("inline") == "inline"
        assert sanitize_css_value("inline-block") == "inline-block"
        assert sanitize_css_value("flex") == "flex"
        assert sanitize_css_value("grid") == "grid"

    def test_allows_width_height(self):
        """width와 height 값을 허용한다."""
        assert sanitize_css_value("100%") == "100%"
        assert sanitize_css_value("200px") == "200px"
        assert sanitize_css_value("auto") == "auto"
        assert sanitize_css_value("max-content") == "max-content"


class TestSanitizeCssValueDangerousKeywords:
    """위험한 CSS 키워드 테스트."""

    def test_blocks_expression(self):
        """expression 키워드를 차단한다."""
        assert sanitize_css_value("expression(alert('xss'))") is None
        assert sanitize_css_value("width: expression(1+1)") is None

    def test_blocks_behavior(self):
        """behavior 키워드를 차단한다."""
        assert sanitize_css_value("behavior: url(xss.htc)") is None
        assert sanitize_css_value("behavior:expression(alert('xss'))") is None

    def test_blocks_at_import(self):
        """@import를 차단한다."""
        assert sanitize_css_value("@import url('http://malicious.com/style.css')") is None
        assert sanitize_css_value("@import 'external.css'") is None

    def test_blocks_at_moz_document(self):
        """@-moz-document를 차단한다."""
        assert sanitize_css_value("@-moz-document url-prefix() { }") is None

    def test_blocks_at_webkit(self):
        """@-webkit-를 차단한다."""
        assert sanitize_css_value("@-webkit-keyframes animation {}") is None

    def test_blocks_at_ms(self):
        """@-ms-를 차단한다."""
        assert sanitize_css_value("@-ms-filter: progid:DXImageTransform.Microsoft") is None

    def test_blocks_keyframes(self):
        """@keyframes를 차단한다."""
        assert sanitize_css_value("@keyframes slide { from { left: 0; } to { left: 100%; } }") is None

    def test_blocks_moz_binding(self):
        """-moz-binding을 차단한다."""
        assert sanitize_css_value("-moz-binding: url(xss.xml#xss)") is None

    def test_blocks_javascript_keyword(self):
        """javascript 키워드를 차단한다."""
        assert sanitize_css_value("javascript:alert('xss')") is None


class TestSanitizeCssValueDangerousFunctions:
    """위험한 CSS 함수 테스트."""

    def test_blocks_url_function_with_javascript(self):
        """javascript: URL을 포함한 url() 함수를 차단한다."""
        assert sanitize_css_value("url(javascript:alert('xss'))") is None
        assert sanitize_css_value("url('javascript:alert(\"xss\")')") is None
        assert sanitize_css_value('url("javascript:alert(\'xss\')")') is None

    def test_blocks_url_function_with_data(self):
        """data: URL을 포함한 url() 함수를 차단한다."""
        assert sanitize_css_value("url(data:text/html,<script>alert('xss')</script>)") is None
        assert sanitize_css_value("url('data:text/html,<img src=x onerror=alert(1)>')") is None

    def test_blocks_url_function_with_vbscript(self):
        """vbscript: URL을 포함한 url() 함수를 차단한다."""
        assert sanitize_css_value("url(vbscript:msgbox('xss'))") is None

    def test_allows_url_function_with_safe_url(self):
        """안전한 URL을 포함한 url() 함수를 허용한다."""
        assert sanitize_css_value("url('/path/to/image.png')") == "url('/path/to/image.png')"
        assert sanitize_css_value("url(https://example.com/image.png)") == "url(https://example.com/image.png)"
        assert sanitize_css_value("url(data:image/png;base64,iVBORw0KGgo=)") is None  # 여전히 차단

    def test_blocks_var_function(self):
        """var() 함수를 차단한다."""
        assert sanitize_css_value("var(--custom-color)") is None
        assert sanitize_css_value("color: var(--primary)") is None

    def test_blocks_expression_function(self):
        """expression() 함수를 차단한다."""
        assert sanitize_css_value("expression(1+1)") is None


class TestSanitizeCssValueUnicodeEscapes:
    """유니코드 이스케이프 테스트."""

    def test_blocks_null_byte_unicode_escape(self):
        """null 바이트 유니코드 이스케이프를 차단한다."""
        assert sanitize_css_value("\\0 color") is None
        assert sanitize_css_value("color: \\0") is None

    def test_blocks_null_byte_with_multiple_zeros(self):
        """여러 0을 포함한 null 바이트를 차단한다."""
        assert sanitize_css_value("\\00 expression") is None
        assert sanitize_css_value("\\000000 alert") is None


class TestSanitizeCssValueComments:
    """CSS 주석 테스트."""

    def test_blocks_css_comments(self):
        """CSS 주석을 차단한다."""
        assert sanitize_css_value("color: red; /* malicious */") is None
        assert sanitize_css_value("/* */ expression /*") is None
        assert sanitize_css_value("color: red */ width: 1000px /*") is None


class TestSanitizeCssValueEdgeCases:
    """CSS 값 엣지 케이스 테스트."""

    def test_empty_string(self):
        """빈 문자열을 처리한다."""
        assert sanitize_css_value("") == ""

    def test_whitespace_only(self):
        """공백만 있는 문자열을 처리한다."""
        assert sanitize_css_value("   ") == "   "

    def test_case_insensitivity_expression(self):
        """expression은 대소문자를 구분하지 않는다."""
        assert sanitize_css_value("EXPRESSION(1+1)") is None
        assert sanitize_css_value("Expression(1+1)") is None
        assert sanitize_css_value("eXpReSSiOn(1+1)") is None

    def test_case_insensitivity_behavior(self):
        """behavior는 대소문자를 구분하지 않는다."""
        assert sanitize_css_value("BEHAVIOR:url()") is None
        assert sanitize_css_value("Behavior:url()") is None

    def test_whitespace_around_keywords(self):
        """키워드 주변의 공백을 처리한다."""
        assert sanitize_css_value("  expression  (1+1)") is None
        assert sanitize_css_value("behavior : url()") is None

    def test_long_safe_css_value(self):
        """긴 안전한 CSS 값을 허용한다."""
        long_value = "rgba(255, 100, 50, 0.9) 10px 20px 30px 40px solid #333 left center"
        assert sanitize_css_value(long_value) == long_value

    def test_multiple_semicolons(self):
        """여러 세미콜론이 있는 CSS를 처리한다."""
        assert sanitize_css_value("color: red;;") == "color: red;;"


class TestSanitizeCssValueComplexCss:
    """복잡한 CSS 값 테스트."""

    def test_shadow_properties(self):
        """box-shadow와 text-shadow를 허용한다."""
        assert sanitize_css_value("0 4px 6px rgba(0, 0, 0, 0.1)") == "0 4px 6px rgba(0, 0, 0, 0.1)"
        assert sanitize_css_value("2px 2px 4px #999") == "2px 2px 4px #999"

    def test_gradient_values(self):
        """gradient 값을 허용한다."""
        # linear-gradient는 url을 포함할 수 있으므로 주의
        assert sanitize_css_value("linear-gradient(to right, red, blue)") == "linear-gradient(to right, red, blue)"

    def test_transform_values(self):
        """transform 값을 허용한다."""
        assert sanitize_css_value("rotate(45deg)") == "rotate(45deg)"
        assert sanitize_css_value("translate(10px, 20px)") == "translate(10px, 20px)"
        assert sanitize_css_value("scale(1.5)") == "scale(1.5)"

    def test_multiple_properties_in_style_attribute(self):
        """스타일 속성에 여러 속성이 있는 경우를 처리한다."""
        value = "color: red; font-size: 14px; padding: 10px"
        assert sanitize_css_value(value) == value

    def test_multiple_properties_with_dangerous_one(self):
        """여러 속성 중 하나가 위험한 경우를 처리한다."""
        value = "color: red; expression(alert('xss')); padding: 10px"
        assert sanitize_css_value(value) is None


class TestSanitizeCssValueSpecialCases:
    """특별한 경우의 CSS 값 테스트."""

    def test_important_declaration(self):
        """!important 선언을 허용한다."""
        assert sanitize_css_value("red !important") == "red !important"
        assert sanitize_css_value("10px !important") == "10px !important"

    def test_calc_function(self):
        """calc() 함수를 허용한다."""
        assert sanitize_css_value("calc(100% - 10px)") == "calc(100% - 10px)"
        assert sanitize_css_value("calc(50px + 10%)") == "calc(50px + 10%)"

    def test_min_max_functions(self):
        """min(), max(), clamp() 함수를 허용한다."""
        assert sanitize_css_value("min(100px, 50vw)") == "min(100px, 50vw)"
        assert sanitize_css_value("max(10px, 5vw)") == "max(10px, 5vw)"
        assert sanitize_css_value("clamp(10px, 5vw, 50px)") == "clamp(10px, 5vw, 50px)"

    def test_percentage_values(self):
        """백분율 값을 허용한다."""
        assert sanitize_css_value("100%") == "100%"
        assert sanitize_css_value("50.5%") == "50.5%"
        assert sanitize_css_value("-10%") == "-10%"

    def test_negative_values(self):
        """음수 값을 허용한다."""
        assert sanitize_css_value("-10px") == "-10px"
        assert sanitize_css_value("-1em") == "-1em"
        assert sanitize_css_value("-50%") == "-50%"

    def test_comma_separated_values(self):
        """쉼표로 구분된 값을 허용한다."""
        assert sanitize_css_value("Arial, sans-serif") == "Arial, sans-serif"
        assert sanitize_css_value("red, blue, green") == "red, blue, green"
