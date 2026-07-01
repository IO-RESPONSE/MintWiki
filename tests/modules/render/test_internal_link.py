"""내부 링크 렌더러 테스트."""
import pytest
from modules.render import render_internal_link


class TestRenderInternalLinkBasic:
    """내부 링크 렌더링 기본 테스트."""

    def test_renders_simple_link(self):
        """단순 링크를 렌더링한다."""
        result = render_internal_link("HelloPage")
        assert result == '<a href="/wiki/HelloPage">HelloPage</a>'

    def test_renders_link_with_label(self):
        """레이블이 있는 링크를 렌더링한다."""
        result = render_internal_link("HelloPage", "Click here")
        assert result == '<a href="/wiki/HelloPage">Click here</a>'

    def test_renders_link_with_spaces_in_name(self):
        """공백이 있는 페이지명 링크를 렌더링한다."""
        result = render_internal_link("Hello Page")
        assert result == '<a href="/wiki/Hello Page">Hello Page</a>'

    def test_renders_link_with_spaces_in_label(self):
        """공백이 있는 레이블로 링크를 렌더링한다."""
        result = render_internal_link("Page", "Click here")
        assert result == '<a href="/wiki/Page">Click here</a>'

    def test_renders_link_with_single_character_page(self):
        """한 글자 페이지명으로 링크를 렌더링한다."""
        result = render_internal_link("A")
        assert result == '<a href="/wiki/A">A</a>'

    def test_renders_link_with_single_character_label(self):
        """한 글자 레이블로 링크를 렌더링한다."""
        result = render_internal_link("Page", "A")
        assert result == '<a href="/wiki/Page">A</a>'


class TestRenderInternalLinkEscaping:
    """내부 링크 HTML 이스케이프 테스트."""

    def test_escapes_ampersand_in_page(self):
        """페이지명의 앰퍼샌드를 이스케이프한다."""
        result = render_internal_link("A & B")
        assert result == '<a href="/wiki/A &amp; B">A &amp; B</a>'

    def test_escapes_ampersand_in_label(self):
        """레이블의 앰퍼샌드를 이스케이프한다."""
        result = render_internal_link("Page", "A & B")
        assert result == '<a href="/wiki/Page">A &amp; B</a>'

    def test_escapes_less_than_in_page(self):
        """페이지명의 <를 이스케이프한다."""
        result = render_internal_link("a < b")
        assert result == '<a href="/wiki/a &lt; b">a &lt; b</a>'

    def test_escapes_less_than_in_label(self):
        """레이블의 <를 이스케이프한다."""
        result = render_internal_link("Page", "a < b")
        assert result == '<a href="/wiki/Page">a &lt; b</a>'

    def test_escapes_greater_than_in_page(self):
        """페이지명의 >를 이스케이프한다."""
        result = render_internal_link("a > b")
        assert result == '<a href="/wiki/a &gt; b">a &gt; b</a>'

    def test_escapes_greater_than_in_label(self):
        """레이블의 >를 이스케이프한다."""
        result = render_internal_link("Page", "a > b")
        assert result == '<a href="/wiki/Page">a &gt; b</a>'

    def test_escapes_double_quote_in_page(self):
        """페이지명의 큰따옴표를 이스케이프한다."""
        result = render_internal_link('He said "hi"')
        assert result == '<a href="/wiki/He said &quot;hi&quot;">He said &quot;hi&quot;</a>'

    def test_escapes_double_quote_in_label(self):
        """레이블의 큰따옴표를 이스케이프한다."""
        result = render_internal_link("Page", 'He said "hi"')
        assert result == '<a href="/wiki/Page">He said &quot;hi&quot;</a>'

    def test_escapes_single_quote_in_page(self):
        """페이지명의 작은따옴표를 이스케이프한다."""
        result = render_internal_link("It's a page")
        assert result == '<a href="/wiki/It&#x27;s a page">It&#x27;s a page</a>'

    def test_escapes_single_quote_in_label(self):
        """레이블의 작은따옴표를 이스케이프한다."""
        result = render_internal_link("Page", "It's a link")
        assert result == '<a href="/wiki/Page">It&#x27;s a link</a>'

    def test_escapes_html_tag_like_page(self):
        """HTML 태그 같은 페이지명을 이스케이프한다."""
        result = render_internal_link("<script>alert('xss')</script>")
        assert result == '<a href="/wiki/&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;">&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</a>'

    def test_escapes_html_tag_like_label(self):
        """HTML 태그 같은 레이블을 이스케이프한다."""
        result = render_internal_link("Page", "<script>alert('xss')</script>")
        assert result == '<a href="/wiki/Page">&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</a>'

    def test_escapes_multiple_special_chars_in_page(self):
        """페이지명의 여러 특수 문자를 이스케이프한다."""
        result = render_internal_link('<div class="test">A & B</div>')
        assert result == '<a href="/wiki/&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;">&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</a>'

    def test_escapes_multiple_special_chars_in_label(self):
        """레이블의 여러 특수 문자를 이스케이프한다."""
        result = render_internal_link("Page", '<div class="test">A & B</div>')
        assert result == '<a href="/wiki/Page">&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</a>'


class TestRenderInternalLinkUnicode:
    """내부 링크 유니코드 테스트."""

    def test_preserves_korean_in_page(self):
        """한글 페이지명을 보존한다."""
        result = render_internal_link("한글페이지")
        assert result == '<a href="/wiki/한글페이지">한글페이지</a>'

    def test_preserves_korean_in_label(self):
        """한글 레이블을 보존한다."""
        result = render_internal_link("Page", "한글 링크")
        assert result == '<a href="/wiki/Page">한글 링크</a>'

    def test_preserves_mixed_languages_in_page(self):
        """혼합 언어 페이지명을 보존한다."""
        result = render_internal_link("Hello 한글 テキスト")
        assert result == '<a href="/wiki/Hello 한글 テキスト">Hello 한글 テキスト</a>'

    def test_preserves_mixed_languages_in_label(self):
        """혼합 언어 레이블을 보존한다."""
        result = render_internal_link("Page", "Hello 한글 テキスト")
        assert result == '<a href="/wiki/Page">Hello 한글 テキスト</a>'

    def test_preserves_emoji_in_page(self):
        """이모지 페이지명을 보존한다."""
        result = render_internal_link("Test 🎉 Page")
        assert result == '<a href="/wiki/Test 🎉 Page">Test 🎉 Page</a>'

    def test_preserves_emoji_in_label(self):
        """이모지 레이블을 보존한다."""
        result = render_internal_link("Page", "Test 🎉 Link")
        assert result == '<a href="/wiki/Page">Test 🎉 Link</a>'


class TestRenderInternalLinkNumbers:
    """내부 링크 숫자 및 기호 테스트."""

    def test_preserves_numbers_in_page(self):
        """페이지명의 숫자를 보존한다."""
        result = render_internal_link("Page 123")
        assert result == '<a href="/wiki/Page 123">Page 123</a>'

    def test_preserves_numbers_in_label(self):
        """레이블의 숫자를 보존한다."""
        result = render_internal_link("Page", "Link 456")
        assert result == '<a href="/wiki/Page">Link 456</a>'

    def test_preserves_safe_punctuation_in_page(self):
        """페이지명의 안전한 구두점을 보존한다."""
        result = render_internal_link("Page-Name_123")
        assert result == '<a href="/wiki/Page-Name_123">Page-Name_123</a>'

    def test_preserves_safe_punctuation_in_label(self):
        """레이블의 안전한 구두점을 보존한다."""
        result = render_internal_link("Page", "Link-Name_123")
        assert result == '<a href="/wiki/Page">Link-Name_123</a>'


class TestRenderInternalLinkEdgeCases:
    """내부 링크 엣지 케이스 테스트."""

    def test_empty_page_name(self):
        """빈 페이지명을 렌더링한다."""
        result = render_internal_link("")
        assert result == '<a href="/wiki/"></a>'

    def test_empty_label_uses_page_name(self):
        """빈 레이블은 페이지명을 사용한다."""
        result = render_internal_link("Page", "")
        # 빈 레이블이 주어지면 그 빈 레이블을 사용
        assert result == '<a href="/wiki/Page"></a>'

    def test_none_label_uses_page_name(self):
        """None 레이블은 페이지명을 사용한다."""
        result = render_internal_link("Page", None)
        assert result == '<a href="/wiki/Page">Page</a>'

    def test_whitespace_only_page(self):
        """공백만 있는 페이지명을 렌더링한다."""
        result = render_internal_link("   ")
        assert result == '<a href="/wiki/   ">   </a>'

    def test_whitespace_only_label(self):
        """공백만 있는 레이블을 렌더링한다."""
        result = render_internal_link("Page", "   ")
        assert result == '<a href="/wiki/Page">   </a>'

    def test_very_long_page_name(self):
        """매우 긴 페이지명을 렌더링한다."""
        long_name = "A" * 1000
        result = render_internal_link(long_name)
        assert result == f'<a href="/wiki/{long_name}">{long_name}</a>'

    def test_very_long_label(self):
        """매우 긴 레이블을 렌더링한다."""
        long_label = "B" * 1000
        result = render_internal_link("Page", long_label)
        assert result == f'<a href="/wiki/Page">{long_label}</a>'

    def test_newline_in_page(self):
        """페이지명의 줄바꿈을 보존한다."""
        result = render_internal_link("Page\nName")
        assert result == '<a href="/wiki/Page\nName">Page\nName</a>'

    def test_newline_in_label(self):
        """레이블의 줄바꿈을 보존한다."""
        result = render_internal_link("Page", "Link\nName")
        assert result == '<a href="/wiki/Page">Link\nName</a>'

    def test_tab_in_page(self):
        """페이지명의 탭을 보존한다."""
        result = render_internal_link("Page\tName")
        assert result == '<a href="/wiki/Page\tName">Page\tName</a>'

    def test_tab_in_label(self):
        """레이블의 탭을 보존한다."""
        result = render_internal_link("Page", "Link\tName")
        assert result == '<a href="/wiki/Page">Link\tName</a>'


class TestRenderInternalLinkHtmlIntegrity:
    """내부 링크 HTML 무결성 테스트."""

    def test_href_attribute_always_quoted(self):
        """href 속성이 항상 큰따옴표로 감싸진다."""
        result = render_internal_link("Page", "Label")
        assert 'href="' in result
        assert '>' in result
        # href 속성이 닫혀 있는지 확인
        assert result.count('"') >= 2

    def test_link_element_always_closed(self):
        """a 태그가 항상 닫혀 있다."""
        result = render_internal_link("Page", "Label")
        assert result.startswith('<a href="')
        assert result.endswith('</a>')

    def test_label_rendered_in_link_text(self):
        """레이블이 링크 텍스트에 올바르게 렌더링된다."""
        result = render_internal_link("Page", "Click Here")
        assert '>Click Here</a>' in result

    def test_page_not_in_label_part_when_different(self):
        """페이지명과 레이블이 다를 때, 페이지명이 링크 텍스트에 나타나지 않는다."""
        result = render_internal_link("ActualPage", "LinkLabel")
        # 링크 텍스트 부분은 LinkLabel만 포함
        assert '>LinkLabel</a>' in result
        # href에는 ActualPage가 포함
        assert 'href="/wiki/ActualPage"' in result
