"""URL 새니타이저 테스트."""
import pytest
from modules.render import sanitize_url


class TestSanitizeUrlSafeSchemes:
    """안전한 스킴 테스트."""

    def test_allows_http_scheme(self):
        """HTTP 스킴을 허용한다."""
        assert sanitize_url("http://example.com") == "http://example.com"

    def test_allows_https_scheme(self):
        """HTTPS 스킴을 허용한다."""
        assert sanitize_url("https://example.com") == "https://example.com"

    def test_allows_ftp_scheme(self):
        """FTP 스킴을 허용한다."""
        assert sanitize_url("ftp://example.com") == "ftp://example.com"

    def test_allows_ftps_scheme(self):
        """FTPS 스킴을 허용한다."""
        assert sanitize_url("ftps://example.com") == "ftps://example.com"

    def test_allows_mailto_scheme(self):
        """mailto 스킴을 허용한다."""
        assert sanitize_url("mailto:user@example.com") == "mailto:user@example.com"

    def test_allows_tel_scheme(self):
        """tel 스킴을 허용한다."""
        assert sanitize_url("tel:+1234567890") == "tel:+1234567890"

    def test_allows_sms_scheme(self):
        """sms 스킴을 허용한다."""
        assert sanitize_url("sms:+1234567890") == "sms:+1234567890"

    def test_allows_geo_scheme(self):
        """geo 스킴을 허용한다."""
        assert sanitize_url("geo:40.7128,-74.0060") == "geo:40.7128,-74.0060"

    def test_allows_safe_scheme_with_path(self):
        """경로가 있는 안전한 스킴을 허용한다."""
        assert sanitize_url("https://example.com/path/to/page") == "https://example.com/path/to/page"

    def test_allows_safe_scheme_with_query_params(self):
        """쿼리 파라미터가 있는 안전한 스킴을 허용한다."""
        assert sanitize_url("https://example.com?foo=bar&baz=qux") == "https://example.com?foo=bar&baz=qux"

    def test_allows_safe_scheme_with_fragment(self):
        """프래그먼트가 있는 안전한 스킴을 허용한다."""
        assert sanitize_url("https://example.com#section") == "https://example.com#section"


class TestSanitizeUrlUnsafeSchemes:
    """안전하지 않은 스킴 테스트."""

    def test_blocks_javascript_scheme(self):
        """javascript 스킴을 차단한다."""
        assert sanitize_url("javascript:alert('xss')") is None

    def test_blocks_javascript_scheme_uppercase(self):
        """대문자 JAVASCRIPT 스킴을 차단한다."""
        assert sanitize_url("JAVASCRIPT:alert('xss')") is None

    def test_blocks_javascript_scheme_mixed_case(self):
        """혼합 대소문자 JavaScript 스킴을 차단한다."""
        assert sanitize_url("JavaScript:alert('xss')") is None

    def test_blocks_data_scheme(self):
        """data 스킴을 차단한다."""
        assert sanitize_url("data:text/html,<script>alert('xss')</script>") is None

    def test_blocks_data_scheme_uppercase(self):
        """대문자 DATA 스킴을 차단한다."""
        assert sanitize_url("DATA:text/html,<script>alert('xss')</script>") is None

    def test_blocks_vbscript_scheme(self):
        """vbscript 스킴을 차단한다."""
        assert sanitize_url("vbscript:msgbox('xss')") is None

    def test_blocks_vbscript_scheme_uppercase(self):
        """대문자 VBSCRIPT 스킴을 차단한다."""
        assert sanitize_url("VBSCRIPT:msgbox('xss')") is None

    def test_blocks_file_scheme(self):
        """file 스킴을 차단한다."""
        assert sanitize_url("file:///etc/passwd") is None


class TestSanitizeUrlRelativeUrls:
    """상대 URL 테스트."""

    def test_allows_relative_path(self):
        """상대 경로를 허용한다."""
        assert sanitize_url("/wiki/Example") == "/wiki/Example"

    def test_allows_relative_path_with_query(self):
        """쿼리가 있는 상대 경로를 허용한다."""
        assert sanitize_url("/wiki/Example?version=2") == "/wiki/Example?version=2"

    def test_allows_relative_path_with_fragment(self):
        """프래그먼트가 있는 상대 경로를 허용한다."""
        assert sanitize_url("/wiki/Example#section") == "/wiki/Example#section"

    def test_allows_dot_slash_relative_path(self):
        """./로 시작하는 상대 경로를 허용한다."""
        assert sanitize_url("./example") == "./example"

    def test_allows_double_dot_relative_path(self):
        """../로 시작하는 상대 경로를 허용한다."""
        assert sanitize_url("../example") == "../example"

    def test_allows_hash_relative_path(self):
        """#로 시작하는 상대 경로를 허용한다."""
        assert sanitize_url("#section") == "#section"


class TestSanitizeUrlEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_string(self):
        """빈 문자열을 처리한다."""
        assert sanitize_url("") == ""

    def test_whitespace_only(self):
        """공백만 있는 문자열을 처리한다."""
        assert sanitize_url("   ") == "   "

    def test_url_with_leading_whitespace_in_scheme(self):
        """스킴 앞의 공백을 차단한다."""
        assert sanitize_url(" javascript:alert('xss')") is None

    def test_url_with_whitespace_in_scheme_middle(self):
        """스킴 중간의 공백을 차단한다."""
        assert sanitize_url("java script:alert('xss')") is None

    def test_url_with_newline_in_scheme(self):
        """스킴에 줄바꿈이 있으면 차단한다."""
        assert sanitize_url("javascript\n:alert('xss')") is None

    def test_url_with_tab_in_scheme(self):
        """스킴에 탭이 있으면 차단한다."""
        assert sanitize_url("javascript\t:alert('xss')") is None

    def test_url_with_multiple_colons(self):
        """여러 콜론이 있는 URL을 처리한다."""
        assert sanitize_url("https://example.com:8080") == "https://example.com:8080"

    def test_url_with_special_characters(self):
        """특수 문자가 있는 안전한 URL을 허용한다."""
        assert sanitize_url("https://example.com/path?q=hello&w=world&special=!@#$%") == "https://example.com/path?q=hello&w=world&special=!@#$%"

    def test_url_with_unicode(self):
        """유니코드가 있는 안전한 URL을 허용한다."""
        assert sanitize_url("https://example.com/한글") == "https://example.com/한글"

    def test_url_with_emoji(self):
        """이모지가 있는 안전한 URL을 허용한다."""
        assert sanitize_url("https://example.com/test-🎉") == "https://example.com/test-🎉"


class TestSanitizeUrlCaseSensitivity:
    """스킴 대소문자 처리 테스트."""

    def test_scheme_case_insensitive(self):
        """스킴 비교는 대소문자를 구분하지 않는다."""
        assert sanitize_url("HTTP://example.com") == "HTTP://example.com"
        assert sanitize_url("HttpS://example.com") == "HttpS://example.com"
        assert sanitize_url("FTP://example.com") == "FTP://example.com"

    def test_dangerous_scheme_case_insensitive(self):
        """위험한 스킴 비교는 대소문자를 구분하지 않는다."""
        assert sanitize_url("JaVaScRiPt:alert('xss')") is None
        assert sanitize_url("DaTa:text/html,<script></script>") is None
        assert sanitize_url("VbScRiPt:msgbox('xss')") is None


class TestSanitizeUrlLongUrls:
    """긴 URL 테스트."""

    def test_allows_very_long_url(self):
        """매우 긴 안전한 URL을 허용한다."""
        long_url = "https://example.com/" + "a" * 1000
        assert sanitize_url(long_url) == long_url

    def test_blocks_long_dangerous_url(self):
        """매우 긴 위험한 URL을 차단한다."""
        long_url = "javascript:" + "a" * 1000
        assert sanitize_url(long_url) is None


class TestSanitizeUrlSchemeValidation:
    """스킴 검증 테스트."""

    def test_url_without_scheme_treated_as_relative(self):
        """스킴이 없는 URL은 상대 경로로 취급한다."""
        assert sanitize_url("example.com") == "example.com"

    def test_url_with_only_scheme_colon(self):
        """스킴 콜론만 있는 URL을 처리한다."""
        assert sanitize_url("https:") == "https:"

    def test_url_with_scheme_and_empty_authority(self):
        """스킴과 빈 기관 부분이 있는 URL을 처리한다."""
        assert sanitize_url("https://") == "https://"
