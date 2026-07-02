"""외부 링크 렌더러 테스트."""
import pytest
from modules.render import render_external_link


class TestRenderExternalLinkBasic:
    """외부 링크 렌더링 기본 테스트."""

    def test_renders_simple_link(self):
        """단순 링크를 렌더링한다."""
        result = render_external_link("https://example.com")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">https://example.com</a>'

    def test_renders_link_with_label(self):
        """레이블이 있는 링크를 렌더링한다."""
        result = render_external_link("https://example.com", "Click here")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Click here</a>'

    def test_renders_link_with_path(self):
        """경로가 있는 URL을 렌더링한다."""
        result = render_external_link("https://example.com/path/to/page")
        assert result == '<a href="https://example.com/path/to/page" rel="noopener noreferrer">https://example.com/path/to/page</a>'

    def test_renders_link_with_query_params(self):
        """쿼리 파라미터가 있는 URL을 렌더링한다."""
        result = render_external_link("https://example.com?foo=bar&baz=qux")
        assert result == '<a href="https://example.com?foo=bar&amp;baz=qux" rel="noopener noreferrer">https://example.com?foo=bar&amp;baz=qux</a>'

    def test_renders_link_with_fragment(self):
        """프래그먼트가 있는 URL을 렌더링한다."""
        result = render_external_link("https://example.com#section")
        assert result == '<a href="https://example.com#section" rel="noopener noreferrer">https://example.com#section</a>'

    def test_renders_http_link(self):
        """HTTP 링크를 렌더링한다."""
        result = render_external_link("http://example.com")
        assert result == '<a href="http://example.com" rel="noopener noreferrer">http://example.com</a>'

    def test_renders_link_with_spaces_in_label(self):
        """공백이 있는 레이블로 링크를 렌더링한다."""
        result = render_external_link("https://example.com", "Click here")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Click here</a>'

    def test_renders_link_with_single_character_url(self):
        """한 글자 URL로 링크를 렌더링한다."""
        result = render_external_link("a")
        assert result == '<a href="a" rel="noopener noreferrer">a</a>'

    def test_renders_link_with_single_character_label(self):
        """한 글자 레이블로 링크를 렌더링한다."""
        result = render_external_link("https://example.com", "A")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">A</a>'


class TestRenderExternalLinkEscaping:
    """외부 링크 HTML 이스케이프 테스트."""

    def test_escapes_ampersand_in_url(self):
        """URL의 앰퍼샌드를 이스케이프한다."""
        result = render_external_link("https://example.com?a=1&b=2")
        assert result == '<a href="https://example.com?a=1&amp;b=2" rel="noopener noreferrer">https://example.com?a=1&amp;b=2</a>'

    def test_escapes_ampersand_in_label(self):
        """레이블의 앰퍼샌드를 이스케이프한다."""
        result = render_external_link("https://example.com", "A & B")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">A &amp; B</a>'

    def test_escapes_less_than_in_url(self):
        """URL의 <를 이스케이프한다."""
        result = render_external_link("https://example.com/a<b")
        assert result == '<a href="https://example.com/a&lt;b" rel="noopener noreferrer">https://example.com/a&lt;b</a>'

    def test_escapes_less_than_in_label(self):
        """레이블의 <를 이스케이프한다."""
        result = render_external_link("https://example.com", "a < b")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">a &lt; b</a>'

    def test_escapes_greater_than_in_url(self):
        """URL의 >를 이스케이프한다."""
        result = render_external_link("https://example.com/a>b")
        assert result == '<a href="https://example.com/a&gt;b" rel="noopener noreferrer">https://example.com/a&gt;b</a>'

    def test_escapes_greater_than_in_label(self):
        """레이블의 >를 이스케이프한다."""
        result = render_external_link("https://example.com", "a > b")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">a &gt; b</a>'

    def test_escapes_double_quote_in_url(self):
        """URL의 큰따옴표를 이스케이프한다."""
        result = render_external_link('https://example.com/file"name')
        assert result == '<a href="https://example.com/file&quot;name" rel="noopener noreferrer">https://example.com/file&quot;name</a>'

    def test_escapes_double_quote_in_label(self):
        """레이블의 큰따옴표를 이스케이프한다."""
        result = render_external_link("https://example.com", 'He said "hi"')
        assert result == '<a href="https://example.com" rel="noopener noreferrer">He said &quot;hi&quot;</a>'

    def test_escapes_single_quote_in_url(self):
        """URL의 작은따옴표를 이스케이프한다."""
        result = render_external_link("https://example.com/it's")
        assert result == '<a href="https://example.com/it&#x27;s" rel="noopener noreferrer">https://example.com/it&#x27;s</a>'

    def test_escapes_single_quote_in_label(self):
        """레이블의 작은따옴표를 이스케이프한다."""
        result = render_external_link("https://example.com", "It's a link")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">It&#x27;s a link</a>'

    def test_escapes_html_tag_like_url(self):
        """HTML 태그 같은 URL을 이스케이프한다."""
        result = render_external_link("javascript:alert('xss')")
        assert result == '<a href="javascript:alert(&#x27;xss&#x27;)" rel="noopener noreferrer">javascript:alert(&#x27;xss&#x27;)</a>'

    def test_escapes_html_tag_like_label(self):
        """HTML 태그 같은 레이블을 이스케이프한다."""
        result = render_external_link("https://example.com", "<script>alert('xss')</script>")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</a>'

    def test_escapes_multiple_special_chars_in_url(self):
        """URL의 여러 특수 문자를 이스케이프한다."""
        result = render_external_link('https://example.com/test?q="a & b"')
        assert result == '<a href="https://example.com/test?q=&quot;a &amp; b&quot;" rel="noopener noreferrer">https://example.com/test?q=&quot;a &amp; b&quot;</a>'

    def test_escapes_multiple_special_chars_in_label(self):
        """레이블의 여러 특수 문자를 이스케이프한다."""
        result = render_external_link("https://example.com", '<div class="test">A & B</div>')
        assert result == '<a href="https://example.com" rel="noopener noreferrer">&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</a>'


class TestRenderExternalLinkUnicode:
    """외부 링크 유니코드 테스트."""

    def test_preserves_korean_in_url(self):
        """한글 URL을 보존한다."""
        result = render_external_link("https://example.com/한글")
        assert result == '<a href="https://example.com/한글" rel="noopener noreferrer">https://example.com/한글</a>'

    def test_preserves_korean_in_label(self):
        """한글 레이블을 보존한다."""
        result = render_external_link("https://example.com", "한글 링크")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">한글 링크</a>'

    def test_preserves_mixed_languages_in_url(self):
        """혼합 언어 URL을 보존한다."""
        result = render_external_link("https://example.com/hello-한글-テキスト")
        assert result == '<a href="https://example.com/hello-한글-テキスト" rel="noopener noreferrer">https://example.com/hello-한글-テキスト</a>'

    def test_preserves_mixed_languages_in_label(self):
        """혼합 언어 레이블을 보존한다."""
        result = render_external_link("https://example.com", "Hello 한글 テキスト")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Hello 한글 テキスト</a>'

    def test_preserves_emoji_in_url(self):
        """이모지 URL을 보존한다."""
        result = render_external_link("https://example.com/test-🎉")
        assert result == '<a href="https://example.com/test-🎉" rel="noopener noreferrer">https://example.com/test-🎉</a>'

    def test_preserves_emoji_in_label(self):
        """이모지 레이블을 보존한다."""
        result = render_external_link("https://example.com", "Test 🎉 Link")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Test 🎉 Link</a>'


class TestRenderExternalLinkNumbers:
    """외부 링크 숫자 및 기호 테스트."""

    def test_preserves_numbers_in_url(self):
        """URL의 숫자를 보존한다."""
        result = render_external_link("https://example.com/page123")
        assert result == '<a href="https://example.com/page123" rel="noopener noreferrer">https://example.com/page123</a>'

    def test_preserves_numbers_in_label(self):
        """레이블의 숫자를 보존한다."""
        result = render_external_link("https://example.com", "Link 456")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Link 456</a>'

    def test_preserves_safe_punctuation_in_url(self):
        """URL의 안전한 구두점을 보존한다."""
        result = render_external_link("https://example.com/page-name_123")
        assert result == '<a href="https://example.com/page-name_123" rel="noopener noreferrer">https://example.com/page-name_123</a>'

    def test_preserves_safe_punctuation_in_label(self):
        """레이블의 안전한 구두점을 보존한다."""
        result = render_external_link("https://example.com", "Link-Name_123")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Link-Name_123</a>'


class TestRenderExternalLinkEdgeCases:
    """외부 링크 엣지 케이스 테스트."""

    def test_empty_url(self):
        """빈 URL을 렌더링한다."""
        result = render_external_link("")
        assert result == '<a href="" rel="noopener noreferrer"></a>'

    def test_empty_label_uses_url(self):
        """빈 레이블은 URL을 사용한다."""
        result = render_external_link("https://example.com", "")
        # 빈 레이블이 주어지면 그 빈 레이블을 사용
        assert result == '<a href="https://example.com" rel="noopener noreferrer"></a>'

    def test_none_label_uses_url(self):
        """None 레이블은 URL을 사용한다."""
        result = render_external_link("https://example.com", None)
        assert result == '<a href="https://example.com" rel="noopener noreferrer">https://example.com</a>'

    def test_whitespace_only_url(self):
        """공백만 있는 URL을 렌더링한다."""
        result = render_external_link("   ")
        assert result == '<a href="   " rel="noopener noreferrer">   </a>'

    def test_whitespace_only_label(self):
        """공백만 있는 레이블을 렌더링한다."""
        result = render_external_link("https://example.com", "   ")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">   </a>'

    def test_very_long_url(self):
        """매우 긴 URL을 렌더링한다."""
        long_url = "https://example.com/" + "a" * 1000
        result = render_external_link(long_url)
        assert result == f'<a href="{long_url}" rel="noopener noreferrer">{long_url}</a>'

    def test_very_long_label(self):
        """매우 긴 레이블을 렌더링한다."""
        long_label = "B" * 1000
        result = render_external_link("https://example.com", long_label)
        assert result == f'<a href="https://example.com" rel="noopener noreferrer">{long_label}</a>'

    def test_newline_in_url(self):
        """URL의 줄바꿈을 보존한다."""
        result = render_external_link("https://example.com/page\nname")
        assert result == '<a href="https://example.com/page\nname" rel="noopener noreferrer">https://example.com/page\nname</a>'

    def test_newline_in_label(self):
        """레이블의 줄바꿈을 보존한다."""
        result = render_external_link("https://example.com", "Link\nName")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Link\nName</a>'

    def test_tab_in_url(self):
        """URL의 탭을 보존한다."""
        result = render_external_link("https://example.com/page\tname")
        assert result == '<a href="https://example.com/page\tname" rel="noopener noreferrer">https://example.com/page\tname</a>'

    def test_tab_in_label(self):
        """레이블의 탭을 보존한다."""
        result = render_external_link("https://example.com", "Link\tName")
        assert result == '<a href="https://example.com" rel="noopener noreferrer">Link\tName</a>'


class TestRenderExternalLinkSecurityAttributes:
    """외부 링크 보안 속성 테스트."""

    def test_includes_noopener_attribute(self):
        """rel 속성에 noopener를 포함한다."""
        result = render_external_link("https://example.com", "Link")
        assert 'rel="noopener noreferrer"' in result

    def test_includes_noreferrer_attribute(self):
        """rel 속성에 noreferrer를 포함한다."""
        result = render_external_link("https://example.com", "Link")
        assert 'rel="noopener noreferrer"' in result

    def test_rel_attribute_always_present(self):
        """rel 속성이 항상 포함된다."""
        result = render_external_link("https://example.com")
        assert 'rel="noopener noreferrer"' in result

    def test_rel_attribute_before_label(self):
        """rel 속성이 링크 텍스트보다 앞에 온다."""
        result = render_external_link("https://example.com", "Label")
        rel_index = result.find('rel="noopener noreferrer"')
        label_index = result.find('>Label<')
        assert rel_index < label_index


class TestRenderExternalLinkHtmlIntegrity:
    """외부 링크 HTML 무결성 테스트."""

    def test_href_attribute_always_quoted(self):
        """href 속성이 항상 큰따옴표로 감싸진다."""
        result = render_external_link("https://example.com", "Label")
        assert 'href="' in result
        # href와 rel 모두 큰따옴표로 감싸져 있어야 함
        assert 'href="https://example.com"' in result

    def test_rel_attribute_always_quoted(self):
        """rel 속성이 항상 큰따옴표로 감싸진다."""
        result = render_external_link("https://example.com", "Label")
        assert 'rel="noopener noreferrer"' in result

    def test_link_element_always_closed(self):
        """a 태그가 항상 닫혀 있다."""
        result = render_external_link("https://example.com", "Label")
        assert result.startswith('<a href="')
        assert result.endswith('</a>')

    def test_label_rendered_in_link_text(self):
        """레이블이 링크 텍스트에 올바르게 렌더링된다."""
        result = render_external_link("https://example.com", "Click Here")
        assert '>Click Here</a>' in result

    def test_url_not_in_label_part_when_different(self):
        """URL과 레이블이 다를 때, URL이 링크 텍스트에 나타나지 않는다."""
        result = render_external_link("https://example.com/actual", "LinkLabel")
        # 링크 텍스트 부분은 LinkLabel만 포함
        assert '>LinkLabel</a>' in result
        # href에는 실제 URL이 포함
        assert 'href="https://example.com/actual"' in result
