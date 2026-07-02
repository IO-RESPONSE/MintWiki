"""렌더 모듈 테스트 픽스처."""
import pytest
from modules.render.model import RenderResult, RenderMetadata, Heading, Footnote


# === 단순 렌더링 스냅샷 ===

@pytest.fixture
def simple_paragraph_html():
    """단순 문단 HTML 스냅샷."""
    return "<p>Hello, World!</p>"


@pytest.fixture
def empty_paragraph_html():
    """빈 문단 HTML 스냅샷."""
    return "<p></p>"


@pytest.fixture
def escaped_paragraph_html():
    """이스케이프된 문단 HTML 스냅샷."""
    return '<p>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</p>'


@pytest.fixture
def simple_heading_h1_html():
    """단순 H1 제목 HTML 스냅샷."""
    return '<h1 id="hello">Hello</h1>'


@pytest.fixture
def simple_heading_h2_html():
    """단순 H2 제목 HTML 스냅샷."""
    return '<h2 id="world">World</h2>'


@pytest.fixture
def heading_with_spaces_html():
    """공백이 있는 제목 HTML 스냅샷."""
    return '<h1 id="hello-world">Hello World</h1>'


@pytest.fixture
def simple_external_link_html():
    """단순 외부 링크 HTML 스냅샷."""
    return '<a href="https://example.com" rel="noopener noreferrer">https://example.com</a>'


@pytest.fixture
def external_link_with_label_html():
    """레이블이 있는 외부 링크 HTML 스냅샷."""
    return '<a href="https://example.com" rel="noopener noreferrer">Click here</a>'


@pytest.fixture
def bold_html():
    """굵은 텍스트 HTML 스냅샷."""
    return "<strong>bold text</strong>"


@pytest.fixture
def italic_html():
    """기울임 텍스트 HTML 스냅샷."""
    return "<em>italic text</em>"


@pytest.fixture
def strike_html():
    """취소선 텍스트 HTML 스냅샷."""
    return "<s>strikethrough text</s>"


@pytest.fixture
def unordered_list_html():
    """비순서 목록 HTML 스냅샷."""
    return "<ul>\n<li>item 1</li>\n<li>item 2</li>\n<li>item 3</li>\n</ul>"


@pytest.fixture
def ordered_list_html():
    """순서 목록 HTML 스냅샷."""
    return "<ol>\n<li>first</li>\n<li>second</li>\n<li>third</li>\n</ol>"


@pytest.fixture
def line_break_html():
    """줄바꿈 HTML 스냅샷."""
    return "<br>"


@pytest.fixture
def code_block_html():
    """코드 블록 HTML 스냅샷."""
    return "<pre><code>print('Hello')</code></pre>"


@pytest.fixture
def simple_table_html():
    """단순 테이블 HTML 스냅샷."""
    return (
        '<table>\n'
        '<thead>\n<tr>\n<th>Header 1</th>\n<th>Header 2</th>\n</tr>\n</thead>\n'
        '<tbody>\n<tr>\n<td>Cell 1</td>\n<td>Cell 2</td>\n</tr>\n</tbody>\n'
        '</table>'
    )


# === 복합 렌더링 스냅샷 ===

@pytest.fixture
def complex_document_html():
    """복합 문서 HTML 스냅샷."""
    return (
        '<h1 id="introduction">Introduction</h1>\n'
        '<p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>\n'
        '<ul>\n<li>item 1</li>\n<li>item 2</li>\n</ul>\n'
        '<h2 id="section-2">Section 2</h2>\n'
        '<p>Another paragraph.</p>'
    )


@pytest.fixture
def document_with_links_html():
    """링크가 있는 문서 HTML 스냅샷."""
    return (
        '<h1 id="links">Links</h1>\n'
        '<p>Check <a href="https://example.com" rel="noopener noreferrer">this link</a> '
        'and <a href="/internal-page" rel="noopener noreferrer">this internal link</a>.</p>'
    )


@pytest.fixture
def document_with_code_html():
    """코드가 포함된 문서 HTML 스냅샷."""
    return (
        '<h1 id="code-example">Code Example</h1>\n'
        '<p>Here is some code:</p>\n'
        '<pre><code>def hello():\n    print("world")</code></pre>'
    )


# === 메타데이터 스냅샷 ===

@pytest.fixture
def render_result_with_headings():
    """제목이 있는 렌더링 결과 스냅샷."""
    metadata = {
        "headings": [
            {"level": 1, "text": "Introduction", "id": "introduction"},
            {"level": 2, "text": "Subsection", "id": "subsection"},
        ],
        "links": [],
        "categories": [],
    }
    return RenderResult(
        html='<h1 id="introduction">Introduction</h1>\n<h2 id="subsection">Subsection</h2>',
        metadata=metadata,
    )


@pytest.fixture
def render_result_with_links():
    """링크가 있는 렌더링 결과 스냅샷."""
    metadata = {
        "headings": [],
        "links": ["https://example.com", "https://another-site.com"],
        "categories": [],
    }
    return RenderResult(
        html='<p><a href="https://example.com" rel="noopener noreferrer">example</a></p>',
        metadata=metadata,
    )


@pytest.fixture
def render_result_with_categories():
    """카테고리가 있는 렌더링 결과 스냅샷."""
    metadata = {
        "headings": [],
        "links": [],
        "categories": ["Category 1", "Category 2"],
    }
    return RenderResult(
        html="<p>Page content</p>",
        metadata=metadata,
    )


@pytest.fixture
def render_result_with_footnotes():
    """각주가 있는 렌더링 결과 스냅샷."""
    metadata = {
        "headings": [],
        "links": [],
        "categories": [],
        "footnotes": [
            {"id": "note1", "text": "First footnote"},
            {"id": "note2", "text": "Second footnote"},
        ],
    }
    return RenderResult(
        html='<p>Text with footnotes<sup><a href="#note1">[1]</a></sup></p>\n'
        '<div class="footnotes">\n'
        '<p><sup id="note1">[1]</sup> First footnote</p>\n'
        '</div>',
        metadata=metadata,
    )


@pytest.fixture
def empty_render_result():
    """빈 렌더링 결과 스냅샷."""
    return RenderResult(html="", metadata={"headings": [], "links": [], "categories": []})


@pytest.fixture
def full_render_result():
    """완전한 렌더링 결과 스냅샷."""
    metadata = {
        "headings": [
            {"level": 1, "text": "Main Title", "id": "main-title"},
            {"level": 2, "text": "Section", "id": "section"},
        ],
        "links": ["https://example.com"],
        "categories": ["Tech", "Tutorial"],
        "footnotes": [
            {"id": "1", "text": "Reference"},
        ],
    }
    return RenderResult(
        html=(
            '<h1 id="main-title">Main Title</h1>\n'
            '<p>Introduction with <a href="https://example.com" rel="noopener noreferrer">link</a></p>\n'
            '<h2 id="section">Section</h2>\n'
            '<p>Content here</p>'
        ),
        metadata=metadata,
    )


# === XSS 방지 스냅샷 ===

@pytest.fixture
def script_injection_escaped():
    """스크립트 주입이 이스케이프된 HTML 스냅샷."""
    return '<p>&lt;script&gt;alert("xss")&lt;/script&gt;</p>'


@pytest.fixture
def onclick_injection_escaped():
    """onclick 속성이 이스케이프된 HTML 스냅샷."""
    return '<p>&lt;img onclick="alert(&#x27;xss&#x27;)" /&gt;</p>'


@pytest.fixture
def data_uri_sanitized():
    """data: URI가 필터링된 HTML 스냅샷."""
    return '<p><a href="#" rel="noopener noreferrer">link</a></p>'


@pytest.fixture
def javascript_protocol_blocked():
    """javascript: 프로토콜이 차단된 HTML 스냅샷."""
    return '<p><a href="#" rel="noopener noreferrer">link</a></p>'


# === 특수 문자 및 인코딩 스냅샷 ===

@pytest.fixture
def korean_text_html():
    """한글 텍스트 HTML 스냅샷."""
    return "<p>한글 텍스트입니다</p>"


@pytest.fixture
def mixed_language_html():
    """혼합 언어 HTML 스냅샷."""
    return "<p>Hello 한글 テキスト</p>"


@pytest.fixture
def emoji_html():
    """이모지 HTML 스냅샷."""
    return "<p>Test 🎉 emoji 👍</p>"


@pytest.fixture
def special_characters_html():
    """특수 문자 HTML 스냅샷."""
    return '<p>A &amp; B &lt; C &gt; D &quot;quote&quot; &#x27;apostrophe&#x27;</p>'


@pytest.fixture
def whitespace_preserved_html():
    """공백이 보존된 HTML 스냅샷."""
    return "<p>line1\nline2\tline3  line4</p>"


# === 목록 스냅샷 ===

@pytest.fixture
def nested_list_html():
    """중첩된 목록 HTML 스냅샷."""
    return (
        "<ul>\n"
        "<li>item 1\n"
        "<ul>\n"
        "<li>nested 1.1</li>\n"
        "<li>nested 1.2</li>\n"
        "</ul>\n"
        "</li>\n"
        "<li>item 2</li>\n"
        "</ul>"
    )


@pytest.fixture
def mixed_list_html():
    """혼합 목록 HTML 스냅샷."""
    return (
        "<ul>\n"
        "<li>unordered 1</li>\n"
        "<li>unordered 2\n"
        "<ol>\n"
        "<li>ordered 2.1</li>\n"
        "<li>ordered 2.2</li>\n"
        "</ol>\n"
        "</li>\n"
        "</ul>"
    )
