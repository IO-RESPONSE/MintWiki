"""렌더 결과 모델 테스트."""
from modules.render.model import RenderResult


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
