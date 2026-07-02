"""렌더 결과 모델 테스트."""
from modules.render.model import RenderResult, RenderMetadata, Heading, Footnote


class TestRenderResultConstruction:
    """렌더링 결과 생성 테스트."""

    def test_creates_render_result_with_empty_html(self):
        """빈 HTML로 렌더링 결과를 생성한다."""
        result = RenderResult(html="", metadata={})
        assert result.html == ""
        assert result.metadata == {}

    def test_creates_render_result_with_html(self):
        """HTML로 렌더링 결과를 생성한다."""
        html = "<p>Hello, World!</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert result.metadata == {}

    def test_creates_render_result_with_multiple_elements(self):
        """여러 요소가 있는 HTML로 렌더링 결과를 생성한다."""
        html = "<h1>Title</h1><p>Content</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert "<h1>" in result.html
        assert "<p>" in result.html

    def test_creates_render_result_with_empty_metadata(self):
        """빈 메타데이터로 렌더링 결과를 생성한다."""
        html = "<p>Test</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert result.metadata == {}

    def test_creates_render_result_with_metadata(self):
        """메타데이터를 포함하여 렌더링 결과를 생성한다."""
        html = "<h1>Title</h1><p>Content</p>"
        metadata = {
            "headings": [{"level": 1, "text": "Title", "id": "title"}],
            "links": ["Document1"],
        }
        result = RenderResult(html=html, metadata=metadata)
        assert result.html == html
        assert result.metadata == metadata
        assert "headings" in result.metadata
        assert "links" in result.metadata

    def test_creates_render_result_with_complex_metadata(self):
        """복잡한 메타데이터를 포함하여 렌더링 결과를 생성한다."""
        html = "<h1>Main</h1><h2>Sub</h2><p>Text</p>"
        metadata = {
            "headings": [
                {"level": 1, "text": "Main", "id": "main"},
                {"level": 2, "text": "Sub", "id": "sub"},
            ],
            "links": ["Document1", "Document2"],
            "categories": ["Category1", "Category2"],
        }
        result = RenderResult(html=html, metadata=metadata)
        assert result.html == html
        assert result.metadata == metadata
        assert len(result.metadata["headings"]) == 2
        assert len(result.metadata["links"]) == 2

    def test_creates_render_result_with_special_characters_in_html(self):
        """특수 문자가 있는 HTML로 렌더링 결과를 생성한다."""
        html = "<p>A &amp; B &lt;test&gt;</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert "&amp;" in result.html
        assert "&lt;" in result.html

    def test_creates_render_result_with_unicode_html(self):
        """유니코드 문자가 있는 HTML로 렌더링 결과를 생성한다."""
        html = "<p>한글 테스트 🎉</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert "한글" in result.html

    def test_creates_render_result_with_multiline_html(self):
        """여러 줄의 HTML로 렌더링 결과를 생성한다."""
        html = """<div>
  <h1>Title</h1>
  <p>Content</p>
</div>"""
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert "\n" in result.html

    def test_metadata_is_independent_copy(self):
        """각 인스턴스의 메타데이터는 독립적이다."""
        metadata1 = {"headings": [{"text": "Title1"}]}
        metadata2 = {"headings": [{"text": "Title2"}]}
        result1 = RenderResult(html="<h1>Title1</h1>", metadata=metadata1)
        result2 = RenderResult(html="<h1>Title2</h1>", metadata=metadata2)
        assert result1.metadata != result2.metadata
        assert result1.metadata["headings"][0]["text"] == "Title1"
        assert result2.metadata["headings"][0]["text"] == "Title2"


class TestRenderResultAttributes:
    """렌더링 결과 속성 테스트."""

    def test_html_attribute_is_string(self):
        """html 속성은 문자열이다."""
        result = RenderResult(html="<p>Test</p>", metadata={})
        assert isinstance(result.html, str)

    def test_metadata_attribute_is_dict(self):
        """metadata 속성은 딕셔너리이다."""
        result = RenderResult(html="<p>Test</p>", metadata={})
        assert isinstance(result.metadata, dict)

    def test_can_access_html_attribute(self):
        """html 속성에 접근할 수 있다."""
        html = "<p>Content</p>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html

    def test_can_access_metadata_attribute(self):
        """metadata 속성에 접근할 수 있다."""
        metadata = {"test": "value"}
        result = RenderResult(html="<p>Test</p>", metadata=metadata)
        assert result.metadata == metadata


class TestRenderResultWithComplexScenarios:
    """렌더링 결과의 복합 시나리오 테스트."""

    def test_render_result_with_table_html(self):
        """테이블이 있는 HTML로 렌더링 결과를 생성한다."""
        html = """<table>
  <tr>
    <td>Cell 1</td>
    <td>Cell 2</td>
  </tr>
</table>"""
        result = RenderResult(html=html, metadata={})
        assert "<table>" in result.html
        assert "<tr>" in result.html

    def test_render_result_with_list_html(self):
        """리스트가 있는 HTML로 렌더링 결과를 생성한다."""
        html = """<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>"""
        result = RenderResult(html=html, metadata={})
        assert "<ul>" in result.html
        assert "<li>" in result.html

    def test_render_result_with_nested_elements(self):
        """중첩된 요소가 있는 HTML로 렌더링 결과를 생성한다."""
        html = "<div><p><span>Nested</span></p></div>"
        result = RenderResult(html=html, metadata={})
        assert result.html == html
        assert "<div>" in result.html
        assert "<span>" in result.html

    def test_render_result_preserves_html_attributes(self):
        """HTML 속성을 보존한다."""
        html = '<a href="http://example.com" title="Link">Example</a>'
        result = RenderResult(html=html, metadata={})
        assert 'href="http://example.com"' in result.html
        assert 'title="Link"' in result.html

    def test_render_result_with_code_block(self):
        """코드 블록이 있는 HTML로 렌더링 결과를 생성한다."""
        html = "<pre><code>print('hello')</code></pre>"
        result = RenderResult(html=html, metadata={})
        assert "<pre>" in result.html
        assert "<code>" in result.html

    def test_render_result_with_extensive_metadata(self):
        """광범위한 메타데이터를 포함하여 렌더링 결과를 생성한다."""
        html = "<h1>Title</h1><p>Content</p>"
        metadata = {
            "headings": [
                {"level": 1, "text": "Title", "id": "title"},
                {"level": 2, "text": "Section", "id": "section"},
            ],
            "links": ["Doc1", "Doc2", "Doc3"],
            "categories": ["Cat1", "Cat2"],
            "footnotes": [{"id": "note1", "text": "Note"}],
        }
        result = RenderResult(html=html, metadata=metadata)
        assert "footnotes" in result.metadata
        assert len(result.metadata["links"]) == 3


class TestHeadingConstruction:
    """제목 메타데이터 생성 테스트."""

    def test_creates_heading_with_basic_info(self):
        """기본 정보로 제목 메타데이터를 생성한다."""
        heading = Heading(level=1, text="Title", id="title")
        assert heading.level == 1
        assert heading.text == "Title"
        assert heading.id == "title"

    def test_creates_heading_with_different_levels(self):
        """다양한 레벨로 제목 메타데이터를 생성한다."""
        heading_h1 = Heading(level=1, text="Main", id="main")
        heading_h2 = Heading(level=2, text="Sub", id="sub")
        heading_h3 = Heading(level=3, text="SubSub", id="subsub")
        assert heading_h1.level == 1
        assert heading_h2.level == 2
        assert heading_h3.level == 3

    def test_creates_heading_with_unicode_text(self):
        """유니코드 텍스트로 제목 메타데이터를 생성한다."""
        heading = Heading(level=1, text="한글 제목", id="korean-title")
        assert heading.text == "한글 제목"
        assert heading.id == "korean-title"

    def test_creates_heading_with_special_id(self):
        """특수 문자가 있는 id로 제목 메타데이터를 생성한다."""
        heading = Heading(level=2, text="Test Section", id="test-section-123")
        assert heading.id == "test-section-123"

    def test_heading_attributes_are_accessible(self):
        """제목 메타데이터의 속성에 접근할 수 있다."""
        heading = Heading(level=3, text="Example", id="example")
        assert isinstance(heading.level, int)
        assert isinstance(heading.text, str)
        assert isinstance(heading.id, str)


class TestFootnoteConstruction:
    """각주 메타데이터 생성 테스트."""

    def test_creates_footnote_with_basic_info(self):
        """기본 정보로 각주 메타데이터를 생성한다."""
        footnote = Footnote(id="note1", text="This is a note")
        assert footnote.id == "note1"
        assert footnote.text == "This is a note"

    def test_creates_footnote_with_different_ids(self):
        """다양한 id로 각주 메타데이터를 생성한다."""
        footnote1 = Footnote(id="note1", text="First note")
        footnote2 = Footnote(id="note2", text="Second note")
        assert footnote1.id == "note1"
        assert footnote2.id == "note2"
        assert footnote1.id != footnote2.id

    def test_creates_footnote_with_unicode_text(self):
        """유니코드 텍스트로 각주 메타데이터를 생성한다."""
        footnote = Footnote(id="note-korean", text="한글 각주")
        assert footnote.text == "한글 각주"

    def test_creates_footnote_with_empty_text(self):
        """빈 텍스트로 각주 메타데이터를 생성한다."""
        footnote = Footnote(id="empty-note", text="")
        assert footnote.text == ""
        assert footnote.id == "empty-note"

    def test_creates_footnote_with_long_text(self):
        """긴 텍스트로 각주 메타데이터를 생성한다."""
        long_text = "This is a very long footnote " * 10
        footnote = Footnote(id="long-note", text=long_text)
        assert footnote.text == long_text
        assert len(footnote.text) > 100

    def test_footnote_attributes_are_accessible(self):
        """각주 메타데이터의 속성에 접근할 수 있다."""
        footnote = Footnote(id="test-note", text="Test text")
        assert isinstance(footnote.id, str)
        assert isinstance(footnote.text, str)


class TestRenderMetadataConstruction:
    """렌더 메타데이터 생성 테스트."""

    def test_creates_empty_render_metadata(self):
        """빈 렌더 메타데이터를 생성한다."""
        metadata = RenderMetadata()
        assert metadata.headings == []
        assert metadata.links == []
        assert metadata.categories == []
        assert metadata.footnotes == []

    def test_creates_render_metadata_with_headings(self):
        """제목 정보를 포함하여 렌더 메타데이터를 생성한다."""
        headings = [
            Heading(level=1, text="Title", id="title"),
            Heading(level=2, text="Section", id="section"),
        ]
        metadata = RenderMetadata(headings=headings)
        assert len(metadata.headings) == 2
        assert metadata.headings[0].text == "Title"
        assert metadata.headings[1].text == "Section"

    def test_creates_render_metadata_with_links(self):
        """링크 목록을 포함하여 렌더 메타데이터를 생성한다."""
        links = ["Document1", "Document2", "Document3"]
        metadata = RenderMetadata(links=links)
        assert len(metadata.links) == 3
        assert "Document1" in metadata.links
        assert "Document2" in metadata.links

    def test_creates_render_metadata_with_categories(self):
        """카테고리 목록을 포함하여 렌더 메타데이터를 생성한다."""
        categories = ["Category1", "Category2"]
        metadata = RenderMetadata(categories=categories)
        assert len(metadata.categories) == 2
        assert "Category1" in metadata.categories
        assert "Category2" in metadata.categories

    def test_creates_render_metadata_with_footnotes(self):
        """각주 정보를 포함하여 렌더 메타데이터를 생성한다."""
        footnotes = [
            Footnote(id="note1", text="First note"),
            Footnote(id="note2", text="Second note"),
        ]
        metadata = RenderMetadata(footnotes=footnotes)
        assert len(metadata.footnotes) == 2
        assert metadata.footnotes[0].id == "note1"
        assert metadata.footnotes[1].id == "note2"

    def test_creates_render_metadata_with_all_fields(self):
        """모든 필드를 포함하여 렌더 메타데이터를 생성한다."""
        headings = [Heading(level=1, text="Main", id="main")]
        links = ["Doc1", "Doc2"]
        categories = ["Category1"]
        footnotes = [Footnote(id="note1", text="Note")]

        metadata = RenderMetadata(
            headings=headings,
            links=links,
            categories=categories,
            footnotes=footnotes,
        )
        assert len(metadata.headings) == 1
        assert len(metadata.links) == 2
        assert len(metadata.categories) == 1
        assert len(metadata.footnotes) == 1

    def test_render_metadata_initializes_empty_lists_by_default(self):
        """기본값으로 빈 리스트를 초기화한다."""
        metadata = RenderMetadata()
        assert isinstance(metadata.headings, list)
        assert isinstance(metadata.links, list)
        assert isinstance(metadata.categories, list)
        assert isinstance(metadata.footnotes, list)

    def test_render_metadata_with_empty_lists(self):
        """빈 리스트로 렌더 메타데이터를 생성한다."""
        metadata = RenderMetadata(
            headings=[],
            links=[],
            categories=[],
            footnotes=[],
        )
        assert metadata.headings == []
        assert metadata.links == []
        assert metadata.categories == []
        assert metadata.footnotes == []

    def test_render_metadata_with_single_elements(self):
        """단일 요소를 포함하여 렌더 메타데이터를 생성한다."""
        metadata = RenderMetadata(
            headings=[Heading(level=1, text="Title", id="title")],
            links=["Doc"],
            categories=["Cat"],
            footnotes=[Footnote(id="n1", text="Note")],
        )
        assert len(metadata.headings) == 1
        assert len(metadata.links) == 1
        assert len(metadata.categories) == 1
        assert len(metadata.footnotes) == 1


class TestRenderMetadataAttributes:
    """렌더 메타데이터 속성 테스트."""

    def test_headings_attribute_is_list(self):
        """headings 속성은 리스트이다."""
        metadata = RenderMetadata()
        assert isinstance(metadata.headings, list)

    def test_links_attribute_is_list(self):
        """links 속성은 리스트이다."""
        metadata = RenderMetadata()
        assert isinstance(metadata.links, list)

    def test_categories_attribute_is_list(self):
        """categories 속성은 리스트이다."""
        metadata = RenderMetadata()
        assert isinstance(metadata.categories, list)

    def test_footnotes_attribute_is_list(self):
        """footnotes 속성은 리스트이다."""
        metadata = RenderMetadata()
        assert isinstance(metadata.footnotes, list)

    def test_can_modify_headings_after_creation(self):
        """생성 후 제목 목록을 수정할 수 있다."""
        metadata = RenderMetadata()
        metadata.headings.append(Heading(level=1, text="New", id="new"))
        assert len(metadata.headings) == 1
        assert metadata.headings[0].text == "New"

    def test_can_modify_links_after_creation(self):
        """생성 후 링크 목록을 수정할 수 있다."""
        metadata = RenderMetadata()
        metadata.links.append("NewLink")
        assert len(metadata.links) == 1
        assert metadata.links[0] == "NewLink"

    def test_can_modify_categories_after_creation(self):
        """생성 후 카테고리 목록을 수정할 수 있다."""
        metadata = RenderMetadata()
        metadata.categories.append("NewCategory")
        assert len(metadata.categories) == 1
        assert metadata.categories[0] == "NewCategory"

    def test_can_modify_footnotes_after_creation(self):
        """생성 후 각주 목록을 수정할 수 있다."""
        metadata = RenderMetadata()
        metadata.footnotes.append(Footnote(id="note1", text="Text"))
        assert len(metadata.footnotes) == 1
        assert metadata.footnotes[0].id == "note1"


class TestRenderMetadataComplexScenarios:
    """렌더 메타데이터 복합 시나리오 테스트."""

    def test_render_metadata_with_multiple_headings(self):
        """여러 레벨의 제목을 포함한다."""
        headings = [
            Heading(level=1, text="Main Title", id="main-title"),
            Heading(level=2, text="Section 1", id="section-1"),
            Heading(level=3, text="Subsection 1.1", id="subsection-11"),
            Heading(level=2, text="Section 2", id="section-2"),
        ]
        metadata = RenderMetadata(headings=headings)
        assert len(metadata.headings) == 4
        h1_count = sum(1 for h in metadata.headings if h.level == 1)
        h2_count = sum(1 for h in metadata.headings if h.level == 2)
        h3_count = sum(1 for h in metadata.headings if h.level == 3)
        assert h1_count == 1
        assert h2_count == 2
        assert h3_count == 1

    def test_render_metadata_independence(self):
        """독립적인 메타데이터 인스턴스들은 서로 영향을 주지 않는다."""
        metadata1 = RenderMetadata(
            headings=[Heading(level=1, text="Title1", id="title1")]
        )
        metadata2 = RenderMetadata(
            headings=[Heading(level=1, text="Title2", id="title2")]
        )
        assert metadata1.headings[0].text == "Title1"
        assert metadata2.headings[0].text == "Title2"
        metadata1.headings.append(Heading(level=2, text="New", id="new"))
        assert len(metadata1.headings) == 2
        assert len(metadata2.headings) == 1

    def test_render_metadata_with_complex_footnotes(self):
        """복잡한 각주 정보를 포함한다."""
        footnotes = [
            Footnote(id="note1", text="Simple footnote"),
            Footnote(id="note2", text="Footnote with special chars: @#$%"),
            Footnote(id="note-korean", text="한글 각주"),
        ]
        metadata = RenderMetadata(footnotes=footnotes)
        assert len(metadata.footnotes) == 3
        assert any(f.id == "note2" for f in metadata.footnotes)
        assert any(f.text == "한글 각주" for f in metadata.footnotes)
