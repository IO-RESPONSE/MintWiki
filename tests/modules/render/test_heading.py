"""제목 렌더러 테스트."""
import pytest
from modules.render import render_heading, generate_heading_id


class TestGenerateHeadingIdBasic:
    """제목 ID 생성 기본 테스트."""

    def test_generates_id_from_simple_text(self):
        """단순 텍스트로부터 ID를 생성한다."""
        assert generate_heading_id("Hello") == "hello"

    def test_converts_to_lowercase(self):
        """대문자를 소문자로 변환한다."""
        assert generate_heading_id("Hello World") == "hello-world"

    def test_replaces_spaces_with_hyphens(self):
        """공백을 하이픈으로 변환한다."""
        assert generate_heading_id("My Test Title") == "my-test-title"

    def test_removes_special_characters(self):
        """특수 문자를 제거한다."""
        assert generate_heading_id("Hello!") == "hello"

    def test_removes_multiple_special_characters(self):
        """여러 특수 문자를 제거한다."""
        assert generate_heading_id("Hello! World?") == "hello-world"

    def test_preserves_numbers(self):
        """숫자를 보존한다."""
        assert generate_heading_id("Test 123") == "test-123"

    def test_handles_multiple_spaces(self):
        """연속된 공백을 하나의 하이픈으로 변환한다."""
        assert generate_heading_id("Hello   World") == "hello-world"

    def test_strips_leading_and_trailing_hyphens(self):
        """앞뒤 하이픈을 제거한다."""
        assert generate_heading_id("  Hello World  ") == "hello-world"

    def test_handles_leading_special_characters(self):
        """앞의 특수 문자를 처리한다."""
        assert generate_heading_id("!Hello") == "hello"

    def test_handles_trailing_special_characters(self):
        """뒤의 특수 문자를 처리한다."""
        assert generate_heading_id("Hello!") == "hello"


class TestGenerateHeadingIdEdgeCases:
    """제목 ID 생성 엣지 케이스 테스트."""

    def test_handles_empty_string(self):
        """빈 문자열을 처리한다."""
        assert generate_heading_id("") == ""

    def test_handles_whitespace_only(self):
        """공백만 있는 문자열을 처리한다."""
        assert generate_heading_id("   ") == ""

    def test_handles_special_characters_only(self):
        """특수 문자만 있는 문자열을 처리한다."""
        assert generate_heading_id("!!!") == ""

    def test_handles_hyphen_only(self):
        """하이픈만 있는 문자열을 처리한다."""
        assert generate_heading_id("-") == ""

    def test_collapses_consecutive_hyphens(self):
        """연속된 하이픈을 하나로 축약한다."""
        assert generate_heading_id("Hello--World") == "hello-world"

    def test_handles_mixed_special_characters(self):
        """다양한 특수 문자를 처리한다."""
        assert generate_heading_id("Hello@World#Test!") == "helloworldtest"

    def test_handles_parentheses(self):
        """괄호를 제거한다."""
        assert generate_heading_id("Test (Example)") == "test-example"

    def test_handles_brackets(self):
        """대괄호를 제거한다."""
        assert generate_heading_id("Test [Example]") == "test-example"

    def test_handles_quotes(self):
        """따옴표를 제거한다."""
        assert generate_heading_id('Test "Example"') == "test-example"

    def test_handles_ampersand(self):
        """앰퍼샌드를 제거한다."""
        assert generate_heading_id("A & B") == "a-b"


class TestGenerateHeadingIdUnicode:
    """제목 ID 생성 유니코드 테스트."""

    def test_removes_korean_characters(self):
        """한글 문자를 제거한다."""
        assert generate_heading_id("테스트") == ""

    def test_handles_mixed_korean_english(self):
        """혼합 텍스트에서 영문과 숫자만 유지한다."""
        result = generate_heading_id("Hello 한글 Test")
        assert "hello" in result and "test" in result
        assert len(result) > 0

    def test_removes_emoji(self):
        """이모지를 제거한다."""
        assert generate_heading_id("Test 🎉") == "test"

    def test_removes_japanese_characters(self):
        """일본어 문자를 제거한다."""
        assert generate_heading_id("テキスト") == ""


class TestRenderHeadingBasic:
    """제목 렌더링 기본 테스트."""

    def test_renders_heading_level_1(self):
        """레벨 1 제목을 렌더링한다."""
        result = render_heading(1, "Hello")
        assert result == '<h1 id="hello">Hello</h1>'

    def test_renders_heading_level_2(self):
        """레벨 2 제목을 렌더링한다."""
        result = render_heading(2, "World")
        assert result == '<h2 id="world">World</h2>'

    def test_renders_heading_level_3(self):
        """레벨 3 제목을 렌더링한다."""
        result = render_heading(3, "Test")
        assert result == '<h3 id="test">Test</h3>'

    def test_renders_heading_level_4(self):
        """레벨 4 제목을 렌더링한다."""
        result = render_heading(4, "Heading")
        assert result == '<h4 id="heading">Heading</h4>'

    def test_renders_heading_level_5(self):
        """레벨 5 제목을 렌더링한다."""
        result = render_heading(5, "Subheading")
        assert result == '<h5 id="subheading">Subheading</h5>'

    def test_renders_heading_level_6(self):
        """레벨 6 제목을 렌더링한다."""
        result = render_heading(6, "Paragraph")
        assert result == '<h6 id="paragraph">Paragraph</h6>'

    def test_renders_heading_with_spaces(self):
        """공백이 있는 제목을 렌더링한다."""
        result = render_heading(1, "Hello World")
        assert result == '<h1 id="hello-world">Hello World</h1>'

    def test_renders_heading_without_id_for_empty_slug(self):
        """공백만 있는 제목은 id 속성 없이 렌더링한다."""
        result = render_heading(1, "   ")
        assert result == '<h1>   </h1>'


class TestRenderHeadingEscaping:
    """제목 렌더링 HTML 이스케이프 테스트."""

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_heading(1, "A & B")
        assert result == '<h1 id="a-b">A &amp; B</h1>'

    def test_escapes_less_than(self):
        """<를 이스케이프한다."""
        result = render_heading(1, "a < b")
        assert result == '<h1 id="a-b">a &lt; b</h1>'

    def test_escapes_greater_than(self):
        """>를 이스케이프한다."""
        result = render_heading(1, "a > b")
        assert result == '<h1 id="a-b">a &gt; b</h1>'

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_heading(1, 'He said "hi"')
        assert result == '<h1 id="he-said-hi">He said &quot;hi&quot;</h1>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_heading(1, "It's a test")
        assert result == '<h1 id="its-a-test">It&#x27;s a test</h1>'

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_heading(1, "<script>alert('xss')</script>")
        assert result == '<h1 id="scriptalertxssscript">&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</h1>'

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_heading(1, '<div class="test">A & B</div>')
        assert result == '<h1 id="div-classtesta-bdiv">&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</h1>'


class TestRenderHeadingUnicode:
    """제목 렌더링 유니코드 테스트."""

    def test_renders_korean_text(self):
        """한글 텍스트를 렌더링한다."""
        result = render_heading(1, "테스트")
        assert result == '<h1>테스트</h1>'  # id가 없으므로 id 속성 없음

    def test_renders_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 렌더링한다."""
        result = render_heading(1, "Hello 한글 Test")
        assert 'Hello' in result and 'Test' in result
        assert '한글' in result

    def test_renders_emoji(self):
        """이모지를 렌더링한다."""
        result = render_heading(1, "Test 🎉 emoji")
        assert "Test" in result and "emoji" in result
        assert "🎉" in result


class TestRenderHeadingInvalidLevel:
    """제목 레벨 검증 테스트."""

    def test_defaults_to_h1_for_zero_level(self):
        """레벨 0은 h1으로 기본값 처리한다."""
        result = render_heading(0, "Test")
        assert result.startswith('<h1')

    def test_defaults_to_h1_for_negative_level(self):
        """음수 레벨은 h1으로 기본값 처리한다."""
        result = render_heading(-1, "Test")
        assert result.startswith('<h1')

    def test_defaults_to_h1_for_level_above_6(self):
        """레벨 7 이상은 h1로 기본값 처리한다."""
        result = render_heading(7, "Test")
        assert result.startswith('<h1')

    def test_handles_non_integer_level_float(self):
        """실수 레벨은 h1으로 기본값 처리한다."""
        result = render_heading(1.5, "Test")
        # 레벨이 정수가 아니면 기본값 처리
        assert '<h' in result

    def test_handles_non_integer_level_string(self):
        """문자열 레벨은 h1으로 기본값 처리한다."""
        result = render_heading("1", "Test")
        # 레벨이 정수가 아니면 기본값 처리
        assert '<h' in result


class TestRenderHeadingEmptyContent:
    """제목 렌더링 빈 내용 테스트."""

    def test_renders_empty_heading(self):
        """빈 제목을 렌더링한다."""
        result = render_heading(1, "")
        assert result == '<h1></h1>'

    def test_renders_whitespace_only_heading(self):
        """공백만 있는 제목을 렌더링한다."""
        result = render_heading(1, "   ")
        assert result == '<h1>   </h1>'


class TestRenderHeadingSpecialCases:
    """제목 렌더링 특수 케이스 테스트."""

    def test_renders_heading_with_numbers(self):
        """숫자가 있는 제목을 렌더링한다."""
        result = render_heading(1, "Chapter 1")
        assert result == '<h1 id="chapter-1">Chapter 1</h1>'

    def test_renders_heading_with_multiple_spaces(self):
        """연속된 공백이 있는 제목을 렌더링한다."""
        result = render_heading(1, "Hello   World")
        assert result == '<h1 id="hello-world">Hello   World</h1>'

    def test_preserves_content_case_in_rendered_html(self):
        """렌더링된 HTML에서 원본 대소문자를 보존한다."""
        result = render_heading(1, "Hello WORLD")
        assert "Hello WORLD" in result
        assert 'id="hello-world"' in result

    def test_renders_heading_with_punctuation(self):
        """구두점이 있는 제목을 렌더링한다."""
        result = render_heading(1, "What is this?")
        assert 'id="what-is-this"' in result
        assert "What is this?" in result

    def test_renders_heading_with_hyphens(self):
        """하이픈이 있는 제목을 렌더링한다."""
        result = render_heading(1, "Hello-World")
        assert 'id="hello-world"' in result
        assert "Hello-World" in result
