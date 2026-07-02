"""카테고리 메타데이터 렌더러 테스트."""
import pytest
from modules.render import render_categories_metadata


class TestRenderCategoriesMetadataBasic:
    """카테고리 메타데이터 렌더링 기본 테스트."""

    def test_renders_single_category(self):
        """단일 카테고리를 렌더링한다."""
        result = render_categories_metadata(["Test"])
        assert 'href="/wiki/Category:Test"' in result
        assert '>Test</a>' in result
        assert 'class="categories-metadata"' in result

    def test_renders_multiple_categories(self):
        """여러 카테고리를 렌더링한다."""
        result = render_categories_metadata(["Wiki", "Technology", "Science"])
        assert 'href="/wiki/Category:Wiki"' in result
        assert 'href="/wiki/Category:Technology"' in result
        assert 'href="/wiki/Category:Science"' in result
        assert '>Wiki</a>' in result
        assert '>Technology</a>' in result
        assert '>Science</a>' in result

    def test_renders_empty_category_list(self):
        """빈 카테고리 목록을 렌더링한다."""
        result = render_categories_metadata([])
        assert result == '<div class="categories-metadata"></div>'

    def test_separates_multiple_categories_with_comma(self):
        """여러 카테고리를 쉼표로 구분한다."""
        result = render_categories_metadata(["A", "B", "C"])
        # 링크들 사이에 쉼표와 공백이 있는지 확인
        assert "</a>, <a" in result

    def test_contains_categories_metadata_div(self):
        """카테고리 메타데이터 div 요소를 포함한다."""
        result = render_categories_metadata(["Test"])
        assert result.startswith('<div class="categories-metadata">')
        assert result.endswith('</div>')

    def test_renders_category_with_single_character(self):
        """한 글자 카테고리명을 렌더링한다."""
        result = render_categories_metadata(["A"])
        assert 'href="/wiki/Category:A"' in result
        assert '>A</a>' in result


class TestRenderCategoriesMetadataEscaping:
    """카테고리 메타데이터 HTML 이스케이프 테스트."""

    def test_escapes_ampersand_in_category(self):
        """카테고리명의 앰퍼샌드를 이스케이프한다."""
        result = render_categories_metadata(["A & B"])
        assert 'href="/wiki/Category:A &amp; B"' in result
        assert '>A &amp; B</a>' in result

    def test_escapes_less_than_in_category(self):
        """카테고리명의 <를 이스케이프한다."""
        result = render_categories_metadata(["a < b"])
        assert 'href="/wiki/Category:a &lt; b"' in result
        assert '>a &lt; b</a>' in result

    def test_escapes_greater_than_in_category(self):
        """카테고리명의 >를 이스케이프한다."""
        result = render_categories_metadata(["a > b"])
        assert 'href="/wiki/Category:a &gt; b"' in result
        assert '>a &gt; b</a>' in result

    def test_escapes_double_quote_in_category(self):
        """카테고리명의 큰따옴표를 이스케이프한다."""
        result = render_categories_metadata(['He said "hi"'])
        assert 'href="/wiki/Category:He said &quot;hi&quot;"' in result
        assert '>He said &quot;hi&quot;</a>' in result

    def test_escapes_single_quote_in_category(self):
        """카테고리명의 작은따옴표를 이스케이프한다."""
        result = render_categories_metadata(["It's a category"])
        assert 'href="/wiki/Category:It&#x27;s a category"' in result
        assert '>It&#x27;s a category</a>' in result

    def test_escapes_html_tag_like_category(self):
        """HTML 태그 같은 카테고리명을 이스케이프한다."""
        result = render_categories_metadata(["<script>alert('xss')</script>"])
        assert 'href="/wiki/Category:&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"' in result
        assert '>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</a>' in result

    def test_escapes_multiple_special_chars_in_category(self):
        """카테고리명의 여러 특수 문자를 이스케이프한다."""
        result = render_categories_metadata(['<div class="test">A & B</div>'])
        assert 'href="/wiki/Category:&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;"' in result
        assert '>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</a>' in result

    def test_escapes_multiple_categories_independently(self):
        """각 카테고리를 독립적으로 이스케이프한다."""
        result = render_categories_metadata(["A & B", "C < D", "E > F"])
        assert 'href="/wiki/Category:A &amp; B"' in result
        assert 'href="/wiki/Category:C &lt; D"' in result
        assert 'href="/wiki/Category:E &gt; F"' in result


class TestRenderCategoriesMetadataUnicode:
    """카테고리 메타데이터 유니코드 테스트."""

    def test_preserves_korean_in_category(self):
        """한글 카테고리명을 보존한다."""
        result = render_categories_metadata(["한글카테고리"])
        assert 'href="/wiki/Category:한글카테고리"' in result
        assert '>한글카테고리</a>' in result

    def test_preserves_mixed_languages_in_category(self):
        """혼합 언어 카테고리명을 보존한다."""
        result = render_categories_metadata(["Hello 한글 テキスト"])
        assert 'href="/wiki/Category:Hello 한글 テキスト"' in result
        assert '>Hello 한글 テキスト</a>' in result

    def test_preserves_emoji_in_category(self):
        """이모지 카테고리명을 보존한다."""
        result = render_categories_metadata(["Test 🎉 Category"])
        assert 'href="/wiki/Category:Test 🎉 Category"' in result
        assert '>Test 🎉 Category</a>' in result


class TestRenderCategoriesMetadataNumbers:
    """카테고리 메타데이터 숫자 및 기호 테스트."""

    def test_preserves_numbers_in_category(self):
        """카테고리명의 숫자를 보존한다."""
        result = render_categories_metadata(["Category 123"])
        assert 'href="/wiki/Category:Category 123"' in result
        assert '>Category 123</a>' in result

    def test_preserves_safe_punctuation_in_category(self):
        """카테고리명의 안전한 구두점을 보존한다."""
        result = render_categories_metadata(["Category-Name_123"])
        assert 'href="/wiki/Category:Category-Name_123"' in result
        assert '>Category-Name_123</a>' in result


class TestRenderCategoriesMetadataEdgeCases:
    """카테고리 메타데이터 엣지 케이스 테스트."""

    def test_empty_category_name(self):
        """빈 카테고리명을 렌더링한다."""
        result = render_categories_metadata([""])
        assert 'href="/wiki/Category:"' in result
        assert 'class="categories-metadata"' in result

    def test_whitespace_only_category(self):
        """공백만 있는 카테고리명을 렌더링한다."""
        result = render_categories_metadata(["   "])
        assert 'href="/wiki/Category:   "' in result
        assert '>   </a>' in result

    def test_very_long_category_name(self):
        """매우 긴 카테고리명을 렌더링한다."""
        long_name = "A" * 1000
        result = render_categories_metadata([long_name])
        assert f'href="/wiki/Category:{long_name}"' in result
        assert f'>{long_name}</a>' in result

    def test_newline_in_category_name(self):
        """카테고리명의 줄바꿈을 보존한다."""
        result = render_categories_metadata(["Category\nName"])
        assert 'href="/wiki/Category:Category\nName"' in result
        assert '>Category\nName</a>' in result

    def test_tab_in_category_name(self):
        """카테고리명의 탭을 보존한다."""
        result = render_categories_metadata(["Category\tName"])
        assert 'href="/wiki/Category:Category\tName"' in result
        assert '>Category\tName</a>' in result

    def test_many_categories(self):
        """많은 수의 카테고리를 렌더링한다."""
        categories = [f"Category{i}" for i in range(100)]
        result = render_categories_metadata(categories)
        for i in range(100):
            assert f'href="/wiki/Category:Category{i}"' in result
            assert f'>Category{i}</a>' in result


class TestRenderCategoriesMetadataHtmlIntegrity:
    """카테고리 메타데이터 HTML 무결성 테스트."""

    def test_href_attributes_always_quoted(self):
        """href 속성이 항상 큰따옴표로 감싸진다."""
        result = render_categories_metadata(["Category"])
        assert 'href="' in result
        # href 속성이 닫혀 있는지 확인
        assert result.count('"') >= 2

    def test_link_elements_always_closed(self):
        """a 태그가 항상 닫혀 있다."""
        result = render_categories_metadata(["Category"])
        assert '<a href="' in result
        assert '</a>' in result

    def test_div_element_always_closed(self):
        """div 태그가 항상 닫혀 있다."""
        result = render_categories_metadata(["Category"])
        assert '<div class="categories-metadata">' in result
        assert '</div>' in result

    def test_categories_rendered_in_link_text(self):
        """카테고리가 링크 텍스트에 올바르게 렌더링된다."""
        result = render_categories_metadata(["Test"])
        assert '>Test</a>' in result

    def test_structure_is_valid(self):
        """렌더링된 HTML 구조가 유효하다."""
        result = render_categories_metadata(["Test"])
        # div 태그가 a 태그를 감싸고 있는지 확인
        assert result.startswith('<div class="categories-metadata">')
        assert result.endswith('</div>')

    def test_structure_with_multiple_categories(self):
        """여러 카테고리의 HTML 구조가 유효하다."""
        result = render_categories_metadata(["A", "B", "C"])
        assert result.startswith('<div class="categories-metadata">')
        assert result.endswith('</div>')
        # 모든 링크가 div 안에 있는지 확인
        assert result.count('<a href="') == 3
        assert result.count('</a>') == 3
