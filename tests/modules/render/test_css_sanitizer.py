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


class TestSanitizeCssValueColors:
    """CSS 색상 값 테스트."""

    def test_allows_named_colors(self):
        """CSS 명명 색상을 허용한다."""
        named_colors = [
            "red", "blue", "green", "white", "black", "yellow",
            "cyan", "magenta", "gray", "silver", "orange", "purple",
            "pink", "brown", "lime", "navy", "teal", "maroon",
            "khaki", "salmon", "gold", "coral", "indigo"
        ]
        for color in named_colors:
            assert sanitize_css_value(color) == color, f"Failed for {color}"
            # 대소문자 혼합도 허용
            assert sanitize_css_value(color.upper()) == color.upper()
            assert sanitize_css_value(color.capitalize()) == color.capitalize()

    def test_allows_hex_colors_short(self):
        """3글자 hex 색상을 허용한다."""
        assert sanitize_css_value("#RGB") == "#RGB"
        assert sanitize_css_value("#000") == "#000"
        assert sanitize_css_value("#FFF") == "#FFF"
        assert sanitize_css_value("#F00") == "#F00"
        assert sanitize_css_value("#abc") == "#abc"
        assert sanitize_css_value("#ABC") == "#ABC"

    def test_allows_hex_colors_long(self):
        """6글자 hex 색상을 허용한다."""
        assert sanitize_css_value("#RRGGBB") == "#RRGGBB"
        assert sanitize_css_value("#000000") == "#000000"
        assert sanitize_css_value("#FFFFFF") == "#FFFFFF"
        assert sanitize_css_value("#FF0000") == "#FF0000"
        assert sanitize_css_value("#00FF00") == "#00FF00"
        assert sanitize_css_value("#0000FF") == "#0000FF"
        assert sanitize_css_value("#abcdef") == "#abcdef"
        assert sanitize_css_value("#ABCDEF") == "#ABCDEF"

    def test_allows_hex_colors_with_alpha(self):
        """8글자 hex 색상 (alpha 포함)을 허용한다."""
        assert sanitize_css_value("#RRGGBBAA") == "#RRGGBBAA"
        assert sanitize_css_value("#00000000") == "#00000000"
        assert sanitize_css_value("#FFFFFFFF") == "#FFFFFFFF"
        assert sanitize_css_value("#FF0000FF") == "#FF0000FF"
        assert sanitize_css_value("#FF0000AA") == "#FF0000AA"
        assert sanitize_css_value("#FF000080") == "#FF000080"
        assert sanitize_css_value("#ffffffff") == "#ffffffff"

    def test_allows_rgb_colors(self):
        """rgb() 색상을 허용한다."""
        assert sanitize_css_value("rgb(255, 0, 0)") == "rgb(255, 0, 0)"
        assert sanitize_css_value("rgb(0, 0, 0)") == "rgb(0, 0, 0)"
        assert sanitize_css_value("rgb(255, 255, 255)") == "rgb(255, 255, 255)"
        assert sanitize_css_value("rgb(100, 150, 200)") == "rgb(100, 150, 200)"
        assert sanitize_css_value("rgb(255,0,0)") == "rgb(255,0,0)"
        assert sanitize_css_value("rgb(255 0 0)") == "rgb(255 0 0)"
        assert sanitize_css_value("rgb(100% 50% 25%)") == "rgb(100% 50% 25%)"

    def test_allows_rgba_colors(self):
        """rgba() 색상을 허용한다."""
        assert sanitize_css_value("rgba(255, 0, 0, 1)") == "rgba(255, 0, 0, 1)"
        assert sanitize_css_value("rgba(255, 0, 0, 0)") == "rgba(255, 0, 0, 0)"
        assert sanitize_css_value("rgba(255, 0, 0, 0.5)") == "rgba(255, 0, 0, 0.5)"
        assert sanitize_css_value("rgba(0, 0, 0, 0.1)") == "rgba(0, 0, 0, 0.1)"
        assert sanitize_css_value("rgba(255,0,0,1)") == "rgba(255,0,0,1)"
        assert sanitize_css_value("rgba(255 0 0 / 0.5)") == "rgba(255 0 0 / 0.5)"
        assert sanitize_css_value("rgba(100% 50% 25% / 0.8)") == "rgba(100% 50% 25% / 0.8)"

    def test_allows_hsl_colors(self):
        """hsl() 색상을 허용한다."""
        assert sanitize_css_value("hsl(0, 100%, 50%)") == "hsl(0, 100%, 50%)"
        assert sanitize_css_value("hsl(120, 100%, 50%)") == "hsl(120, 100%, 50%)"
        assert sanitize_css_value("hsl(240, 100%, 50%)") == "hsl(240, 100%, 50%)"
        assert sanitize_css_value("hsl(0, 0%, 0%)") == "hsl(0, 0%, 0%)"
        assert sanitize_css_value("hsl(360, 100%, 100%)") == "hsl(360, 100%, 100%)"
        assert sanitize_css_value("hsl(45deg, 50%, 75%)") == "hsl(45deg, 50%, 75%)"
        assert sanitize_css_value("hsl(45 50% 75%)") == "hsl(45 50% 75%)"

    def test_allows_hsla_colors(self):
        """hsla() 색상을 허용한다."""
        assert sanitize_css_value("hsla(0, 100%, 50%, 1)") == "hsla(0, 100%, 50%, 1)"
        assert sanitize_css_value("hsla(120, 100%, 50%, 0.5)") == "hsla(120, 100%, 50%, 0.5)"
        assert sanitize_css_value("hsla(240, 100%, 50%, 0)") == "hsla(240, 100%, 50%, 0)"
        assert sanitize_css_value("hsla(0, 0%, 0%, 0.1)") == "hsla(0, 0%, 0%, 0.1)"
        assert sanitize_css_value("hsla(45deg, 50%, 75%, 0.8)") == "hsla(45deg, 50%, 75%, 0.8)"
        assert sanitize_css_value("hsla(45 50% 75% / 0.5)") == "hsla(45 50% 75% / 0.5)"

    def test_allows_special_color_keywords(self):
        """특별한 색상 키워드를 허용한다."""
        assert sanitize_css_value("transparent") == "transparent"
        assert sanitize_css_value("currentColor") == "currentColor"
        assert sanitize_css_value("currentcolor") == "currentcolor"
        assert sanitize_css_value("inherit") == "inherit"
        assert sanitize_css_value("initial") == "initial"
        assert sanitize_css_value("unset") == "unset"
        assert sanitize_css_value("revert") == "revert"

    def test_allows_hwb_colors(self):
        """hwb() 색상을 허용한다."""
        assert sanitize_css_value("hwb(0 0% 0%)") == "hwb(0 0% 0%)"
        assert sanitize_css_value("hwb(120 10% 20%)") == "hwb(120 10% 20%)"
        assert sanitize_css_value("hwb(240deg 30% 40%)") == "hwb(240deg 30% 40%)"
        assert sanitize_css_value("hwb(45, 25%, 15%)") == "hwb(45, 25%, 15%)"

    def test_allows_lab_colors(self):
        """lab() 색상을 허용한다."""
        assert sanitize_css_value("lab(50 20 30)") == "lab(50 20 30)"
        assert sanitize_css_value("lab(100% 10 -20)") == "lab(100% 10 -20)"
        assert sanitize_css_value("lab(75.5 10.5 -5.5)") == "lab(75.5 10.5 -5.5)"

    def test_allows_lch_colors(self):
        """lch() 색상을 허용한다."""
        assert sanitize_css_value("lch(50 30 180)") == "lch(50 30 180)"
        assert sanitize_css_value("lch(100% 50 45deg)") == "lch(100% 50 45deg)"
        assert sanitize_css_value("lch(75.5 25.5 120)") == "lch(75.5 25.5 120)"

    def test_allows_color_function(self):
        """color() 함수를 허용한다."""
        assert sanitize_css_value("color(display-p3 1 0 0)") == "color(display-p3 1 0 0)"
        assert sanitize_css_value("color(srgb 1 0 0)") == "color(srgb 1 0 0)"
        assert sanitize_css_value("color(rec2020 0.5 0.2 0.8)") == "color(rec2020 0.5 0.2 0.8)"

    def test_allows_color_mix_function(self):
        """color-mix() 함수를 허용한다."""
        assert sanitize_css_value("color-mix(in srgb, red 50%, blue)") == "color-mix(in srgb, red 50%, blue)"
        assert sanitize_css_value("color-mix(in hsl, hsl(0 100% 50%) 80%, white)") == "color-mix(in hsl, hsl(0 100% 50%) 80%, white)"

    def test_color_values_with_spaces(self):
        """공백이 포함된 색상 값을 처리한다."""
        assert sanitize_css_value("  red  ") == "  red  "
        assert sanitize_css_value("  #FF0000  ") == "  #FF0000  "
        assert sanitize_css_value("  rgb(255, 0, 0)  ") == "  rgb(255, 0, 0)  "

    def test_color_values_case_insensitivity(self):
        """색상 함수는 대소문자를 구분하지 않는다."""
        assert sanitize_css_value("RGB(255, 0, 0)") == "RGB(255, 0, 0)"
        assert sanitize_css_value("RGBA(255, 0, 0, 0.5)") == "RGBA(255, 0, 0, 0.5)"
        assert sanitize_css_value("HSL(0, 100%, 50%)") == "HSL(0, 100%, 50%)"
        assert sanitize_css_value("HSLA(120, 50%, 50%, 1)") == "HSLA(120, 50%, 50%, 1)"
        assert sanitize_css_value("HWB(45, 10%, 20%)") == "HWB(45, 10%, 20%)"
        assert sanitize_css_value("LAB(50 20 30)") == "LAB(50 20 30)"
        assert sanitize_css_value("LCH(50 30 180)") == "LCH(50 30 180)"

    def test_color_with_alpha_in_rgb(self):
        """RGB 함수에서 alpha 채널이 있는 경우를 처리한다."""
        assert sanitize_css_value("rgb(255, 0, 0, 0.5)") == "rgb(255, 0, 0, 0.5)"
        assert sanitize_css_value("rgb(255 0 0 / 50%)") == "rgb(255 0 0 / 50%)"

    def test_invalid_but_safe_color_values(self):
        """렌더링되지 않지만 안전한 색상 값을 허용한다."""
        # 유효하지 않은 색상이지만 보안 위협이 없음
        assert sanitize_css_value("notacolor") == "notacolor"
        assert sanitize_css_value("reddish") == "reddish"
        assert sanitize_css_value("#GGGGGG") == "#GGGGGG"
        assert sanitize_css_value("rgb(300, 300, 300)") == "rgb(300, 300, 300)"

    def test_color_values_with_units(self):
        """단위가 포함된 색상 값을 처리한다."""
        assert sanitize_css_value("rgb(255deg, 0rad, 0grad)") == "rgb(255deg, 0rad, 0grad)"
        assert sanitize_css_value("hsl(45turn, 50%, 75%)") == "hsl(45turn, 50%, 75%)"

    def test_color_gradients_with_colors(self):
        """색상을 포함한 gradient를 허용한다."""
        assert sanitize_css_value("linear-gradient(to right, red, blue)") == "linear-gradient(to right, red, blue)"
        assert sanitize_css_value("linear-gradient(45deg, #FF0000, #0000FF)") == "linear-gradient(45deg, #FF0000, #0000FF)"
        assert sanitize_css_value("radial-gradient(circle, rgba(255,0,0,1), rgba(0,0,255,1))") == "radial-gradient(circle, rgba(255,0,0,1), rgba(0,0,255,1))"
        assert sanitize_css_value("conic-gradient(from 45deg, red, blue, green)") == "conic-gradient(from 45deg, red, blue, green)"

    def test_multiple_colors_in_value(self):
        """여러 색상이 있는 값을 처리한다."""
        assert sanitize_css_value("red blue green") == "red blue green"
        assert sanitize_css_value("#FF0000, #00FF00, #0000FF") == "#FF0000, #00FF00, #0000FF"
        assert sanitize_css_value("rgb(255,0,0) rgba(0,255,0,0.5) hsl(240,100%,50%)") == "rgb(255,0,0) rgba(0,255,0,0.5) hsl(240,100%,50%)"

    def test_color_with_alpha_unit_variations(self):
        """Alpha 채널의 다양한 단위 형식을 처리한다."""
        assert sanitize_css_value("rgba(255, 0, 0, 100%)") == "rgba(255, 0, 0, 100%)"
        assert sanitize_css_value("rgba(255, 0, 0, 0%)") == "rgba(255, 0, 0, 0%)"
        assert sanitize_css_value("rgba(255, 0, 0, 50%)") == "rgba(255, 0, 0, 50%)"

    def test_hsl_with_turn_unit(self):
        """HSL에서 turn 단위를 처리한다."""
        assert sanitize_css_value("hsl(0.5turn, 100%, 50%)") == "hsl(0.5turn, 100%, 50%)"
        assert sanitize_css_value("hsl(1turn, 50%, 50%)") == "hsl(1turn, 50%, 50%)"
        assert sanitize_css_value("hsla(0.25turn, 75%, 25%, 0.8)") == "hsla(0.25turn, 75%, 25%, 0.8)"

    def test_color_values_should_not_contain_expression(self):
        """색상 값에 expression을 포함하면 차단한다."""
        assert sanitize_css_value("rgb(expression(255), 0, 0)") is None
        assert sanitize_css_value("hsl(expression(0), 100%, 50%)") is None
        assert sanitize_css_value("#000 expression()") is None

    def test_color_values_should_not_contain_url(self):
        """색상 값에 위험한 url()을 포함하면 차단한다."""
        assert sanitize_css_value("rgb(255, url(javascript:alert()), 0)") is None
        assert sanitize_css_value("hsl(url(data:...), 50%, 50%)") is None
        assert sanitize_css_value("color: red url(javascript:)") is None

    def test_color_values_should_not_contain_var_function(self):
        """색상 값에 var()을 포함하면 차단한다."""
        assert sanitize_css_value("var(--color)") is None
        assert sanitize_css_value("rgb(var(--red), 0, 0)") is None
        assert sanitize_css_value("hsl(var(--hue), 100%, 50%)") is None


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
