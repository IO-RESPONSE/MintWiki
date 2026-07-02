"""각주 섹션 렌더러 테스트."""
import pytest
from modules.render import render_footnotes_section


class TestRenderFootnotesSectionBasic:
    """각주 섹션 렌더링 기본 테스트."""

    def test_renders_single_footnote(self):
        """단일 각주를 렌더링한다."""
        result = render_footnotes_section(["Test footnote"])
        assert 'id="footnote-1"' in result
        assert '>Test footnote</li>' in result
        assert 'class="footnotes-section"' in result
        assert '<ol>' in result
        assert '</ol>' in result

    def test_renders_multiple_footnotes(self):
        """여러 각주를 렌더링한다."""
        result = render_footnotes_section(["First", "Second", "Third"])
        assert 'id="footnote-1"' in result
        assert 'id="footnote-2"' in result
        assert 'id="footnote-3"' in result
        assert '>First</li>' in result
        assert '>Second</li>' in result
        assert '>Third</li>' in result

    def test_renders_empty_footnote_list(self):
        """빈 각주 목록을 렌더링한다."""
        result = render_footnotes_section([])
        assert result == '<div class="footnotes-section"></div>'

    def test_footnotes_are_ordered_list(self):
        """각주가 순서 있는 목록으로 렌더링된다."""
        result = render_footnotes_section(["A", "B", "C"])
        assert result.count('<li id=') == 3
        assert result.count('</li>') == 3

    def test_contains_footnotes_section_div(self):
        """각주 섹션 div 요소를 포함한다."""
        result = render_footnotes_section(["Test"])
        assert result.startswith('<div class="footnotes-section">')
        assert result.endswith('</div>')

    def test_footnote_id_increments(self):
        """각주 id가 순차적으로 증가한다."""
        result = render_footnotes_section(["A", "B", "C", "D", "E"])
        for i in range(1, 6):
            assert f'id="footnote-{i}"' in result


class TestRenderFootnotesSectionEscaping:
    """각주 섹션 HTML 이스케이프 테스트."""

    def test_escapes_ampersand_in_footnote(self):
        """각주의 앰퍼샌드를 이스케이프한다."""
        result = render_footnotes_section(["A & B"])
        assert '>A &amp; B</li>' in result

    def test_escapes_less_than_in_footnote(self):
        """각주의 <를 이스케이프한다."""
        result = render_footnotes_section(["a < b"])
        assert '>a &lt; b</li>' in result

    def test_escapes_greater_than_in_footnote(self):
        """각주의 >를 이스케이프한다."""
        result = render_footnotes_section(["a > b"])
        assert '>a &gt; b</li>' in result

    def test_escapes_double_quote_in_footnote(self):
        """각주의 큰따옴표를 이스케이프한다."""
        result = render_footnotes_section(['He said "hi"'])
        assert '>He said &quot;hi&quot;</li>' in result

    def test_escapes_single_quote_in_footnote(self):
        """각주의 작은따옴표를 이스케이프한다."""
        result = render_footnotes_section(["It's a footnote"])
        assert '>It&#x27;s a footnote</li>' in result

    def test_escapes_html_tag_like_footnote(self):
        """HTML 태그 같은 각주를 이스케이프한다."""
        result = render_footnotes_section(["<script>alert('xss')</script>"])
        assert '>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</li>' in result

    def test_escapes_multiple_special_chars_in_footnote(self):
        """각주의 여러 특수 문자를 이스케이프한다."""
        result = render_footnotes_section(['<div class="test">A & B</div>'])
        assert '>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</li>' in result

    def test_escapes_multiple_footnotes_independently(self):
        """각 각주를 독립적으로 이스케이프한다."""
        result = render_footnotes_section(["A & B", "C < D", "E > F"])
        assert '>A &amp; B</li>' in result
        assert '>C &lt; D</li>' in result
        assert '>E &gt; F</li>' in result


class TestRenderFootnotesSectionUnicode:
    """각주 섹션 유니코드 테스트."""

    def test_preserves_korean_in_footnote(self):
        """한글 각주를 보존한다."""
        result = render_footnotes_section(["한글각주"])
        assert '>한글각주</li>' in result

    def test_preserves_mixed_languages_in_footnote(self):
        """혼합 언어 각주를 보존한다."""
        result = render_footnotes_section(["Hello 한글 テキスト"])
        assert '>Hello 한글 テキスト</li>' in result

    def test_preserves_emoji_in_footnote(self):
        """이모지 각주를 보존한다."""
        result = render_footnotes_section(["Test 🎉 footnote"])
        assert '>Test 🎉 footnote</li>' in result


class TestRenderFootnotesSectionNumbers:
    """각주 섹션 숫자 및 기호 테스트."""

    def test_preserves_numbers_in_footnote(self):
        """각주의 숫자를 보존한다."""
        result = render_footnotes_section(["Footnote 123"])
        assert '>Footnote 123</li>' in result

    def test_preserves_safe_punctuation_in_footnote(self):
        """각주의 안전한 구두점을 보존한다."""
        result = render_footnotes_section(["Footnote-Name_123"])
        assert '>Footnote-Name_123</li>' in result


class TestRenderFootnotesSectionEdgeCases:
    """각주 섹션 엣지 케이스 테스트."""

    def test_empty_footnote_text(self):
        """빈 각주를 렌더링한다."""
        result = render_footnotes_section([""])
        assert 'id="footnote-1"' in result
        assert 'class="footnotes-section"' in result

    def test_whitespace_only_footnote(self):
        """공백만 있는 각주를 렌더링한다."""
        result = render_footnotes_section(["   "])
        assert 'id="footnote-1"' in result
        assert '>   </li>' in result

    def test_very_long_footnote_text(self):
        """매우 긴 각주를 렌더링한다."""
        long_text = "A" * 1000
        result = render_footnotes_section([long_text])
        assert f'>{long_text}</li>' in result

    def test_newline_in_footnote(self):
        """각주의 줄바꿈을 보존한다."""
        result = render_footnotes_section(["Footnote\nText"])
        assert '>Footnote\nText</li>' in result

    def test_tab_in_footnote(self):
        """각주의 탭을 보존한다."""
        result = render_footnotes_section(["Footnote\tText"])
        assert '>Footnote\tText</li>' in result

    def test_many_footnotes(self):
        """많은 수의 각주를 렌더링한다."""
        footnotes = [f"Footnote {i}" for i in range(100)]
        result = render_footnotes_section(footnotes)
        for i in range(1, 101):
            assert f'id="footnote-{i}"' in result
            assert f'>Footnote {i-1}</li>' in result


class TestRenderFootnotesSectionHtmlIntegrity:
    """각주 섹션 HTML 무결성 테스트."""

    def test_id_attributes_always_present(self):
        """id 속성이 항상 존재한다."""
        result = render_footnotes_section(["Footnote"])
        assert 'id="footnote-1"' in result

    def test_li_elements_always_closed(self):
        """li 태그가 항상 닫혀 있다."""
        result = render_footnotes_section(["Footnote"])
        assert '<li' in result
        assert '</li>' in result

    def test_ol_element_always_closed(self):
        """ol 태그가 항상 닫혀 있다."""
        result = render_footnotes_section(["Footnote"])
        assert '<ol>' in result
        assert '</ol>' in result

    def test_div_element_always_closed(self):
        """div 태그가 항상 닫혀 있다."""
        result = render_footnotes_section(["Footnote"])
        assert '<div class="footnotes-section">' in result
        assert '</div>' in result

    def test_footnotes_rendered_in_list_items(self):
        """각주가 li 요소에 올바르게 렌더링된다."""
        result = render_footnotes_section(["Test"])
        assert '>Test</li>' in result

    def test_structure_is_valid(self):
        """렌더링된 HTML 구조가 유효하다."""
        result = render_footnotes_section(["Test"])
        # div 태그가 ol 태그를 감싸고 있는지 확인
        assert result.startswith('<div class="footnotes-section">')
        assert result.endswith('</div>')

    def test_structure_with_multiple_footnotes(self):
        """여러 각주의 HTML 구조가 유효하다."""
        result = render_footnotes_section(["A", "B", "C"])
        assert result.startswith('<div class="footnotes-section">')
        assert result.endswith('</div>')
        # 모든 li가 ol 안에 있는지 확인
        assert result.count('<li') == 3
        assert result.count('</li>') == 3
