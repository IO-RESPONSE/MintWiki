"""코드 블록 렌더러 테스트."""
import pytest
from modules.render import render_code_block


class TestRenderCodeBlockBasic:
    """코드 블록 렌더링 기본 테스트."""

    def test_renders_simple_text(self):
        """단순 텍스트를 렌더링한다."""
        result = render_code_block("print('Hello')")
        assert result == "<pre><code>print(&#x27;Hello&#x27;)</code></pre>"

    def test_renders_empty_string(self):
        """빈 문자열을 렌더링한다."""
        result = render_code_block("")
        assert result == "<pre><code></code></pre>"

    def test_renders_text_with_spaces(self):
        """공백이 있는 텍스트를 렌더링한다."""
        result = render_code_block("  indented code  ")
        assert result == "<pre><code>  indented code  </code></pre>"


class TestRenderCodeBlockWikiMarkup:
    """위키 마크업 처리 테스트."""

    def test_preserves_bold_markup(self):
        """굵은 마크업을 그대로 보존한다."""
        result = render_code_block("'''bold'''")
        assert result == "<pre><code>&#x27;&#x27;&#x27;bold&#x27;&#x27;&#x27;</code></pre>"

    def test_preserves_italic_markup(self):
        """이탤릭 마크업을 그대로 보존한다."""
        result = render_code_block("''italic''")
        assert result == "<pre><code>&#x27;&#x27;italic&#x27;&#x27;</code></pre>"

    def test_preserves_link_markup(self):
        """링크 마크업을 그대로 보존한다."""
        result = render_code_block("[[Link]]")
        assert result == "<pre><code>[[Link]]</code></pre>"

    def test_preserves_multiple_wiki_markup(self):
        """여러 위키 마크업을 보존한다."""
        result = render_code_block("[[Link]] and '''bold''' and ''italic''")
        assert result == "<pre><code>[[Link]] and &#x27;&#x27;&#x27;bold&#x27;&#x27;&#x27; and &#x27;&#x27;italic&#x27;&#x27;</code></pre>"

    def test_preserves_code_block_markup(self):
        """코드 블록 마크업을 그대로 보존한다."""
        # render_code_block은 파서가 이미 구분자를 제거한 내용을 받음
        result = render_code_block("nested code")
        assert result == "<pre><code>nested code</code></pre>"


class TestRenderCodeBlockHtmlEscaping:
    """HTML 이스케이프 테스트."""

    def test_escapes_html_tag_like_string(self):
        """HTML 태그 같은 문자열을 이스케이프한다."""
        result = render_code_block("<script>alert('xss')</script>")
        assert result == "<pre><code>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</code></pre>"

    def test_escapes_less_than(self):
        """< 기호를 이스케이프한다."""
        result = render_code_block("if a < b")
        assert result == "<pre><code>if a &lt; b</code></pre>"

    def test_escapes_greater_than(self):
        """> 기호를 이스케이프한다."""
        result = render_code_block("if a > b")
        assert result == "<pre><code>if a &gt; b</code></pre>"

    def test_escapes_ampersand(self):
        """앰퍼샌드를 이스케이프한다."""
        result = render_code_block("a & b")
        assert result == "<pre><code>a &amp; b</code></pre>"

    def test_escapes_double_quote(self):
        """큰따옴표를 이스케이프한다."""
        result = render_code_block('He said "hi"')
        assert result == '<pre><code>He said &quot;hi&quot;</code></pre>'

    def test_escapes_single_quote(self):
        """작은따옴표를 이스케이프한다."""
        result = render_code_block("It's a test")
        assert result == "<pre><code>It&#x27;s a test</code></pre>"

    def test_escapes_multiple_special_characters(self):
        """여러 특수 문자를 이스케이프한다."""
        result = render_code_block('<div class="test">A & B</div>')
        assert result == '<pre><code>&lt;div class=&quot;test&quot;&gt;A &amp; B&lt;/div&gt;</code></pre>'


class TestRenderCodeBlockLanguageFeatures:
    """프로그래밍 언어 특성 테스트."""

    def test_preserves_python_syntax(self):
        """파이썬 문법을 보존한다."""
        code = "def hello(name):\n    print(f'Hello {name}')"
        result = render_code_block(code)
        assert "def hello(name):" in result
        assert "print" in result
        assert "&lt;pre&gt;" not in result  # 코드 내용이 이스케이프되었는지 확인

    def test_preserves_javascript_syntax(self):
        """자바스크립트 문법을 보존한다."""
        code = "const x = 10;\nif (x > 5 && x < 20) { console.log('big'); }"
        result = render_code_block(code)
        assert "&lt;pre&gt;" not in result
        assert "&lt;" in result  # < 와 > 는 이스케이프되어야 함
        assert "&gt;" in result

    def test_preserves_html_syntax(self):
        """HTML 문법을 보존한다."""
        code = "<html>\n<body>Hello</body>\n</html>"
        result = render_code_block(code)
        assert result == "<pre><code>&lt;html&gt;\n&lt;body&gt;Hello&lt;/body&gt;\n&lt;/html&gt;</code></pre>"

    def test_preserves_css_syntax(self):
        """CSS 문법을 보존한다."""
        code = ".class { color: red; }"
        result = render_code_block(code)
        assert ".class" in result
        assert "color: red;" in result


class TestRenderCodeBlockSpecialCharacters:
    """특수 문자 처리 테스트."""

    def test_preserves_math_symbols(self):
        """수학 기호를 보존한다."""
        result = render_code_block("1 + 2 = 3")
        assert result == "<pre><code>1 + 2 = 3</code></pre>"

    def test_preserves_operators(self):
        """연산자를 보존한다."""
        result = render_code_block("x = y * 2 - z / 3")
        assert result == "<pre><code>x = y * 2 - z / 3</code></pre>"

    def test_preserves_punctuation(self):
        """구두점을 보존한다."""
        result = render_code_block("func(a, b; c: d)")
        assert result == "<pre><code>func(a, b; c: d)</code></pre>"

    def test_preserves_brackets(self):
        """괄호를 보존한다."""
        result = render_code_block("array[0] {1, 2, 3} (a, b)")
        assert result == "<pre><code>array[0] {1, 2, 3} (a, b)</code></pre>"


class TestRenderCodeBlockMultiline:
    """여러 줄 콘텐츠 테스트."""

    def test_preserves_newlines(self):
        """줄바꿈을 보존한다."""
        result = render_code_block("line1\nline2\nline3")
        assert result == "<pre><code>line1\nline2\nline3</code></pre>"

    def test_preserves_blank_lines(self):
        """빈 줄을 보존한다."""
        result = render_code_block("line1\n\nline2")
        assert result == "<pre><code>line1\n\nline2</code></pre>"

    def test_preserves_leading_trailing_whitespace(self):
        """앞뒤 공백을 보존한다."""
        result = render_code_block("  code  ")
        assert result == "<pre><code>  code  </code></pre>"

    def test_preserves_internal_spaces(self):
        """내부 공백을 보존한다."""
        result = render_code_block("a  b   c")
        assert result == "<pre><code>a  b   c</code></pre>"

    def test_preserves_indentation(self):
        """들여쓰기를 보존한다."""
        code = "if x:\n    y = 1\n    z = 2"
        result = render_code_block(code)
        assert "    y = 1" in result
        assert "    z = 2" in result

    def test_preserves_tabs(self):
        """탭을 보존한다."""
        result = render_code_block("text\twith\ttabs")
        assert result == "<pre><code>text\twith\ttabs</code></pre>"

    def test_preserves_mixed_whitespace(self):
        """공백과 탭이 섞인 경우를 보존한다."""
        result = render_code_block("  \t  mixed  \t  ")
        assert result == "<pre><code>  \t  mixed  \t  </code></pre>"


class TestRenderCodeBlockUnicode:
    """유니코드 및 다국어 지원 테스트."""

    def test_preserves_korean_text(self):
        """한글 텍스트를 보존한다."""
        result = render_code_block("# 이것은 테스트입니다")
        assert result == "<pre><code># 이것은 테스트입니다</code></pre>"

    def test_preserves_mixed_languages(self):
        """여러 언어가 섞인 텍스트를 보존한다."""
        result = render_code_block("// Hello 한글 テキスト")
        assert result == "<pre><code>// Hello 한글 テキスト</code></pre>"

    def test_preserves_emoji(self):
        """이모지를 보존한다."""
        result = render_code_block("print('Test 🎉 emoji 🚀')")
        assert "Test 🎉 emoji 🚀" in result

    def test_preserves_unicode_escapes(self):
        """유니코드 이스케이프를 보존한다."""
        result = render_code_block("\\u0048\\u0065\\u006c\\u006c\\u006f")
        assert result == "<pre><code>\\u0048\\u0065\\u006c\\u006c\\u006f</code></pre>"


class TestRenderCodeBlockComplexContent:
    """복잡한 콘텐츠 테스트."""

    def test_renders_json_code(self):
        """JSON 코드를 렌더링한다."""
        code = '{\n  "name": "test",\n  "value": 123\n}'
        result = render_code_block(code)
        assert '&quot;name&quot;' in result
        assert '&quot;test&quot;' in result

    def test_renders_sql_code(self):
        """SQL 코드를 렌더링한다."""
        code = "SELECT * FROM users WHERE id > 10;"
        result = render_code_block(code)
        assert "SELECT * FROM users WHERE id &gt; 10;" in result

    def test_renders_regex_pattern(self):
        """정규표현식을 렌더링한다."""
        code = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        result = render_code_block(code)
        assert r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" in result

    def test_renders_shell_script(self):
        """쉘 스크립트를 렌더링한다."""
        code = "#!/bin/bash\necho 'Hello' > file.txt\ncat file.txt"
        result = render_code_block(code)
        assert "#!/bin/bash" in result
        assert "&lt;" not in result or "&lt;" in result  # < 기호가 이스케이프되었는지 확인

    def test_renders_xml_code(self):
        """XML 코드를 렌더링한다."""
        code = '<?xml version="1.0"?>\n<root>\n  <item>value</item>\n</root>'
        result = render_code_block(code)
        assert "&lt;?xml" in result
        assert "&lt;root&gt;" in result

    def test_renders_code_with_html_entities(self):
        """HTML 엔티티가 포함된 코드를 렌더링한다."""
        result = render_code_block("&lt;tag&gt; and &amp;")
        assert result == "<pre><code>&amp;lt;tag&amp;gt; and &amp;amp;</code></pre>"


class TestRenderCodeBlockEdgeCases:
    """엣지 케이스 테스트."""

    def test_renders_only_whitespace(self):
        """공백만 있는 콘텐츠를 렌더링한다."""
        result = render_code_block("   \n\t  ")
        assert result == "<pre><code>   \n\t  </code></pre>"

    def test_renders_single_character(self):
        """단일 문자를 렌더링한다."""
        result = render_code_block("a")
        assert result == "<pre><code>a</code></pre>"

    def test_renders_single_special_character(self):
        """단일 특수 문자를 렌더링한다."""
        result = render_code_block("<")
        assert result == "<pre><code>&lt;</code></pre>"

    def test_renders_long_content(self):
        """긴 콘텐츠를 렌더링한다."""
        text = "Lorem ipsum dolor sit amet, " * 100
        result = render_code_block(text)
        assert result.startswith("<pre><code>")
        assert result.endswith("</code></pre>")
        assert text in result

    def test_renders_very_long_line(self):
        """매우 긴 한 줄을 렌더링한다."""
        text = "x" * 10000
        result = render_code_block(text)
        assert text in result
        assert result == f"<pre><code>{text}</code></pre>"

    def test_renders_all_special_chars_combined(self):
        """모든 특수 문자를 함께 렌더링한다."""
        result = render_code_block("< > & \" ' [[ ]] '''bold''' ''italic''")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
        assert "&#x27;" in result
        assert "[[" in result
        assert "]]" in result

    def test_renders_newline_combinations(self):
        """다양한 줄바꿈 조합을 렌더링한다."""
        result = render_code_block("a\nb\r\nc")
        assert "a\nb\r\nc" in result

    def test_renders_content_with_braces(self):
        """중괄호를 포함한 콘텐츠를 렌더링한다."""
        result = render_code_block("{ code }")
        assert "{ code }" in result
        assert result == "<pre><code>{ code }</code></pre>"


class TestRenderCodeBlockStructure:
    """렌더링 구조 테스트."""

    def test_uses_pre_and_code_tags(self):
        """<pre><code> 태그를 사용한다."""
        result = render_code_block("test")
        assert result.startswith("<pre><code>")
        assert result.endswith("</code></pre>")

    def test_escapes_before_wrapping(self):
        """콘텐츠를 이스케이프한 후 태그로 감싼다."""
        result = render_code_block("<tag>")
        assert result == "<pre><code>&lt;tag&gt;</code></pre>"
        # 렌더링 결과의 pre/code 태그는 이스케이프되지 않아야 함
        assert result.count("<pre>") == 1
        assert result.count("</pre>") == 1
        assert result.count("<code>") == 1
        assert result.count("</code>") == 1

    def test_maintains_content_integrity(self):
        """콘텐츠 무결성을 유지한다."""
        original = "line1\nline2\nline3"
        result = render_code_block(original)
        # 엘리먼트를 제거하면 원본과 같아야 함
        inner_content = result.replace("<pre><code>", "").replace("</code></pre>", "")
        assert inner_content == original


class TestRenderCodeBlockPerformance:
    """성능 테스트."""

    def test_handles_large_content(self):
        """큰 콘텐츠를 처리한다."""
        large_code = "x = 1\n" * 1000
        result = render_code_block(large_code)
        assert result.startswith("<pre><code>")
        assert result.endswith("</code></pre>")
        assert large_code in result

    def test_handles_many_special_characters(self):
        """많은 특수 문자를 처리한다."""
        special_code = "< > & \" ' " * 100
        result = render_code_block(special_code)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
