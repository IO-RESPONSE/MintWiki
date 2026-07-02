"""리다이렉트 공지 렌더러 테스트."""
import pytest
from modules.render import render_redirect_notice


class TestRenderRedirectNoticeBasic:
    """리다이렉트 공지 렌더링 기본 테스트."""

    def test_renders_simple_redirect_notice(self):
        """단순 리다이렉트 공지를 렌더링한다."""
        result = render_redirect_notice("TargetPage")
        assert 'href="/wiki/TargetPage"' in result
        assert '>TargetPage</a>' in result
        assert '→' in result

    def test_renders_redirect_notice_with_spaces_in_target(self):
        """공백이 있는 대상 페이지명 리다이렉트 공지를 렌더링한다."""
        result = render_redirect_notice("Target Page")
        assert 'href="/wiki/Target Page"' in result
        assert '>Target Page</a>' in result

    def test_renders_redirect_notice_with_single_character(self):
        """한 글자 페이지명으로 리다이렉트 공지를 렌더링한다."""
        result = render_redirect_notice("A")
        assert 'href="/wiki/A"' in result
        assert '>A</a>' in result

    def test_contains_redirect_notice_div(self):
        """리다이렉트 공지 div 요소를 포함한다."""
        result = render_redirect_notice("Page")
        assert result.startswith('<div class="redirect-notice">')
        assert result.endswith('</div>')

    def test_contains_arrow_symbol(self):
        """화살표 기호를 포함한다."""
        result = render_redirect_notice("Page")
        assert '→' in result


class TestRenderRedirectNoticeEscaping:
    """리다이렉트 공지 HTML 이스케이프 테스트."""

    def test_escapes_ampersand_in_target(self):
        """대상 페이지명의 앰퍼샌드를 이스케이프한다."""
        result = render_redirect_notice("A & B")
        assert 'href="/wiki/A &amp; B"' in result
        assert '>A &amp; B</a>' in result

    def test_escapes_less_than_in_target(self):
        """대상 페이지명의 <를 이스케이프한다."""
        result = render_redirect_notice("a < b")
        assert 'href="/wiki/a &lt; b"' in result
        assert '>a &lt; b</a>' in result

    def test_escapes_greater_than_in_target(self):
        """대상 페이지명의 >를 이스케이프한다."""
        result = render_redirect_notice("a > b")
        assert 'href="/wiki/a &gt; b"' in result
        assert '>a &gt; b</a>' in result

    def test_escapes_double_quote_in_target(self):
        """대상 페이지명의 큰따옴표를 이스케이프한다."""
        result = render_redirect_notice('He said "hi"')
        assert 'href="/wiki/He said &quot;hi&quot;"' in result
        assert '>He said &quot;hi&quot;</a>' in result

    def test_escapes_single_quote_in_target(self):
        """대상 페이지명의 작은따옴표를 이스케이프한다."""
        result = render_redirect_notice("It's a page")
        assert 'href="/wiki/It&#x27;s a page"' in result
        assert '>It&#x27;s a page</a>' in result

    def test_escapes_html_tag_like_target(self):
        """HTML 태그 같은 대상 페이지명을 이스케이프한다."""
        result = render_redirect_notice("<script>alert('xss')</script>")
        assert 'href="/wiki/&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"' in result
        assert '>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</a>' in result

    def test_escapes_multiple_special_chars_in_target(self):
        """대상 페이지명의 여러 특수 문자를 이스케이프한다."""
        result = render_redirect_notice('<div class="test">A & B</div>')
        assert 'href="/wiki/&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;"' in result
        assert '>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</a>' in result


class TestRenderRedirectNoticeUnicode:
    """리다이렉트 공지 유니코드 테스트."""

    def test_preserves_korean_in_target(self):
        """한글 대상 페이지명을 보존한다."""
        result = render_redirect_notice("한글페이지")
        assert 'href="/wiki/한글페이지"' in result
        assert '>한글페이지</a>' in result

    def test_preserves_mixed_languages_in_target(self):
        """혼합 언어 대상 페이지명을 보존한다."""
        result = render_redirect_notice("Hello 한글 テキスト")
        assert 'href="/wiki/Hello 한글 テキスト"' in result
        assert '>Hello 한글 テキスト</a>' in result

    def test_preserves_emoji_in_target(self):
        """이모지 대상 페이지명을 보존한다."""
        result = render_redirect_notice("Test 🎉 Page")
        assert 'href="/wiki/Test 🎉 Page"' in result
        assert '>Test 🎉 Page</a>' in result


class TestRenderRedirectNoticeNumbers:
    """리다이렉트 공지 숫자 및 기호 테스트."""

    def test_preserves_numbers_in_target(self):
        """대상 페이지명의 숫자를 보존한다."""
        result = render_redirect_notice("Page 123")
        assert 'href="/wiki/Page 123"' in result
        assert '>Page 123</a>' in result

    def test_preserves_safe_punctuation_in_target(self):
        """대상 페이지명의 안전한 구두점을 보존한다."""
        result = render_redirect_notice("Page-Name_123")
        assert 'href="/wiki/Page-Name_123"' in result
        assert '>Page-Name_123</a>' in result


class TestRenderRedirectNoticeEdgeCases:
    """리다이렉트 공지 엣지 케이스 테스트."""

    def test_empty_target_page(self):
        """빈 대상 페이지명을 렌더링한다."""
        result = render_redirect_notice("")
        assert 'href="/wiki/"' in result
        assert 'class="redirect-notice"' in result

    def test_whitespace_only_target(self):
        """공백만 있는 대상 페이지명을 렌더링한다."""
        result = render_redirect_notice("   ")
        assert 'href="/wiki/   "' in result
        assert '>   </a>' in result

    def test_very_long_target_page_name(self):
        """매우 긴 대상 페이지명을 렌더링한다."""
        long_name = "A" * 1000
        result = render_redirect_notice(long_name)
        assert f'href="/wiki/{long_name}"' in result
        assert f'>{long_name}</a>' in result

    def test_newline_in_target_page(self):
        """대상 페이지명의 줄바꿈을 보존한다."""
        result = render_redirect_notice("Page\nName")
        assert 'href="/wiki/Page\nName"' in result
        assert '>Page\nName</a>' in result

    def test_tab_in_target_page(self):
        """대상 페이지명의 탭을 보존한다."""
        result = render_redirect_notice("Page\tName")
        assert 'href="/wiki/Page\tName"' in result
        assert '>Page\tName</a>' in result


class TestRenderRedirectNoticeHtmlIntegrity:
    """리다이렉트 공지 HTML 무결성 테스트."""

    def test_href_attribute_always_quoted(self):
        """href 속성이 항상 큰따옴표로 감싸진다."""
        result = render_redirect_notice("Page")
        assert 'href="' in result
        # href 속성이 닫혀 있는지 확인
        assert result.count('"') >= 2

    def test_link_element_always_closed(self):
        """a 태그가 항상 닫혀 있다."""
        result = render_redirect_notice("Page")
        assert '<a href="' in result
        assert '</a>' in result

    def test_div_element_always_closed(self):
        """div 태그가 항상 닫혀 있다."""
        result = render_redirect_notice("Page")
        assert '<div class="redirect-notice">' in result
        assert '</div>' in result

    def test_target_rendered_in_link_text(self):
        """대상이 링크 텍스트에 올바르게 렌더링된다."""
        result = render_redirect_notice("Target")
        assert '>Target</a>' in result

    def test_structure_is_valid(self):
        """렌더링된 HTML 구조가 유효하다."""
        result = render_redirect_notice("Page")
        # div 태그가 a 태그를 감싸고 있는지 확인
        assert result.startswith('<div class="redirect-notice">→ <a href=')
        assert result.endswith('</a></div>')
