"""평문 텍스트 블록 파서 테스트."""
import pytest
from modules.parser import PlainTextBlockParser
from modules.parser.model import ParserResult


class TestPlainTextBlockParserParse:
    """PlainTextBlockParser의 parse 메서드 테스트."""

    def test_parses_empty_source(self):
        """빈 소스 텍스트를 파싱한다."""
        result = PlainTextBlockParser.parse("")
        assert isinstance(result, ParserResult)
        assert result.blocks == []
        assert result.metadata["links"] == []
        assert result.metadata["categories"] == []

    def test_parses_single_line_text(self):
        """단일 줄 평문을 파싱한다."""
        result = PlainTextBlockParser.parse("Hello, World!")
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "Hello, World!"

    def test_parses_multiple_consecutive_lines(self):
        """연속된 여러 줄을 하나의 블록으로 파싱한다."""
        source = "First line\nSecond line\nThird line"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "First line\nSecond line\nThird line"

    def test_parses_multiple_blocks_separated_by_blank_line(self):
        """빈 줄로 분리된 여러 블록을 파싱한다."""
        source = "First paragraph\n\nSecond paragraph"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["content"] == "First paragraph"
        assert result.blocks[1]["content"] == "Second paragraph"

    def test_parses_multiple_blocks_with_multiple_blank_lines(self):
        """여러 개의 빈 줄로 분리된 블록들을 파싱한다."""
        source = "First\n\n\nSecond\n\n\nThird"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["content"] == "First"
        assert result.blocks[1]["content"] == "Second"
        assert result.blocks[2]["content"] == "Third"

    def test_ignores_leading_whitespace(self):
        """첫 줄 앞의 빈 줄을 무시한다."""
        source = "\n\nFirst paragraph\n\nSecond paragraph"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["content"] == "First paragraph"
        assert result.blocks[1]["content"] == "Second paragraph"

    def test_ignores_trailing_whitespace(self):
        """마지막 줄 뒤의 빈 줄을 무시한다."""
        source = "First paragraph\n\nSecond paragraph\n\n"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["content"] == "First paragraph"
        assert result.blocks[1]["content"] == "Second paragraph"

    def test_handles_whitespace_only_source(self):
        """공백만 있는 소스를 파싱한다."""
        source = "   \n\n   \n"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks == []

    def test_parses_block_with_internal_whitespace(self):
        """내부 공백을 포함한 블록을 파싱한다."""
        source = "Line one  \nLine two\t\nLine three"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Line one  \nLine two\t\nLine three"

    def test_returns_parser_result_with_metadata(self):
        """파싱 결과에 메타데이터를 포함한다."""
        result = PlainTextBlockParser.parse("Test content")
        assert isinstance(result, ParserResult)
        assert "links" in result.metadata
        assert "categories" in result.metadata
        assert "headings" in result.metadata
        assert result.metadata["links"] == []
        assert result.metadata["categories"] == []
        assert result.metadata["headings"] == []

    def test_parses_complex_multi_block_document(self):
        """복잡한 다중 블록 문서를 파싱한다."""
        source = (
            "Introduction paragraph.\n"
            "This is the first block.\n"
            "\n"
            "Second paragraph starts here.\n"
            "It continues on the next line.\n"
            "\n"
            "Third and final block."
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["content"] == "Introduction paragraph.\nThis is the first block."
        assert result.blocks[1]["content"] == "Second paragraph starts here.\nIt continues on the next line."
        assert result.blocks[2]["content"] == "Third and final block."


class TestPlainTextBlockParserIntegration:
    """PlainTextBlockParser와 ParserResult의 통합 테스트."""

    def test_parser_result_attributes_are_accessible(self):
        """파싱 결과의 속성에 접근할 수 있다."""
        result = PlainTextBlockParser.parse("Test\n\nContent")
        assert hasattr(result, 'blocks')
        assert hasattr(result, 'metadata')
        assert isinstance(result.blocks, list)
        assert isinstance(result.metadata, dict)

    def test_all_blocks_have_type_and_content(self):
        """모든 블록이 타입과 내용을 가진다."""
        result = PlainTextBlockParser.parse("First\n\nSecond")
        for block in result.blocks:
            assert "type" in block
            assert "content" in block
            assert block["type"] == "paragraph"
            assert isinstance(block["content"], str)


class TestPlainTextBlockParserEscapedHtml:
    """PlainTextBlockParser의 이스케이프된 HTML 처리 테스트."""

    def test_parses_escaped_html_entities(self):
        """이스케이프된 HTML 엔티티를 포함한 텍스트를 파싱한다."""
        source = "This has &lt;tag&gt; in it."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This has &lt;tag&gt; in it."
        assert result.blocks[0]["has_escaped_html"] is True

    def test_marks_block_with_escaped_html_flag(self):
        """이스케이프된 HTML을 포함한 블록에 플래그를 설정한다."""
        source = "Text with &amp; ampersand."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["has_escaped_html"] is True

    def test_recognizes_common_html_entities(self):
        """일반적인 HTML 엔티티를 인식한다."""
        source = "Use &lt; &gt; &amp; &quot; &apos; entities."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["has_escaped_html"] is True

    def test_recognizes_numeric_html_entities(self):
        """숫자 HTML 엔티티를 인식한다."""
        source = "Decimal &#65; and hex &#x41; entities."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["has_escaped_html"] is True

    def test_no_escaped_html_flag_for_plain_text(self):
        """평문에는 이스케이프된 HTML 플래그를 설정하지 않는다."""
        source = "This is plain text without any HTML entities."
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]

    def test_multiple_blocks_with_escaped_html(self):
        """여러 블록 중 일부만 이스케이프된 HTML을 포함할 수 있다."""
        source = "First block.\n\nSecond with &lt;tag&gt;.\n\nThird plain."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert "has_escaped_html" not in result.blocks[0]
        assert result.blocks[1]["has_escaped_html"] is True
        assert "has_escaped_html" not in result.blocks[2]

    def test_escaped_html_in_multiline_block(self):
        """여러 줄 블록에서 이스케이프된 HTML을 인식한다."""
        source = "First line\nSecond line with &nbsp; entity\nThird line."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["has_escaped_html"] is True


class TestPlainTextBlockParserHeadingsLevelOne:
    """PlainTextBlockParser의 제목 수준 1 파싱 테스트."""

    def test_parses_heading_level_one(self):
        """제목 수준 1을 파싱한다."""
        source = "= Title ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 1
        assert result.blocks[0]["content"] == "Title"

    def test_heading_with_extra_spaces(self):
        """여러 개의 공백이 있는 제목을 파싱한다."""
        source = "=  Title  ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 1
        assert result.blocks[0]["content"] == "Title"

    def test_heading_followed_by_paragraph(self):
        """제목 다음에 문단이 있는 경우를 파싱한다."""
        source = "= Title =\n\nContent here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 1
        assert result.blocks[0]["content"] == "Title"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Content here."

    def test_multiple_headings_with_paragraphs(self):
        """여러 제목과 문단을 파싱한다."""
        source = "= First =\n\nFirst content.\n\n= Second ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["content"] == "First"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "First content."
        assert result.blocks[2]["type"] == "heading"
        assert result.blocks[2]["content"] == "Second"

    def test_heading_metadata_extraction(self):
        """제목 메타데이터를 추출한다."""
        source = "= Main Title ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["headings"]) == 1
        assert result.metadata["headings"][0]["level"] == 1
        assert result.metadata["headings"][0]["text"] == "Main Title"

    def test_multiple_headings_in_metadata(self):
        """여러 제목의 메타데이터를 추출한다."""
        source = "= Title One =\n\nText.\n\n= Title Two ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["headings"]) == 2
        assert result.metadata["headings"][0]["text"] == "Title One"
        assert result.metadata["headings"][1]["text"] == "Title Two"

    def test_heading_with_special_characters(self):
        """특수 문자가 있는 제목을 파싱한다."""
        source = "= Title with: Special & Characters! ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Title with: Special & Characters!"

    def test_heading_with_numbers(self):
        """숫자가 있는 제목을 파싱한다."""
        source = "= Chapter 1: Introduction ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Chapter 1: Introduction"

    def test_paragraph_not_matching_heading_pattern(self):
        """제목 패턴과 일치하지 않는 텍스트는 문단으로 취급한다."""
        source = "= Title with no closing"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "= Title with no closing"

    def test_single_equal_signs_not_heading(self):
        """한 개의 등호 기호는 제목으로 취급하지 않는다."""
        source = "=Not a title"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"

    def test_headings_do_not_have_escaped_html_flag(self):
        """제목 블록은 이스케이프된 HTML 플래그를 갖지 않는다."""
        source = "= Title ="
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]


class TestPlainTextBlockParserInternalLinks:
    """PlainTextBlockParser의 내부 링크 파싱 테스트."""

    def test_parses_single_internal_link(self):
        """단일 내부 링크를 파싱한다."""
        source = "See [[Document1]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0] == "Document1"

    def test_parses_multiple_internal_links(self):
        """여러 내부 링크를 파싱한다."""
        source = "See [[Link1]] and [[Link2]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 2
        assert "Link1" in result.metadata["links"]
        assert "Link2" in result.metadata["links"]

    def test_extracts_categories(self):
        """카테고리를 추출한다."""
        source = "[[Category:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Test"

    def test_extracts_multiple_categories(self):
        """여러 카테고리를 추출한다."""
        source = "[[Category:Wiki]]\n\nSome content."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert "Wiki" in result.metadata["categories"]

    def test_extracts_redirects(self):
        """리다이렉트를 추출한다."""
        source = "[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert len(result.metadata["redirects"]) == 1
        assert result.metadata["redirects"][0]["to"] == "NewPage"

    def test_internal_links_in_paragraph(self):
        """문단 안의 내부 링크를 파싱한다."""
        source = "This paragraph mentions [[Link1]] and [[Link2]]."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This paragraph mentions [[Link1]] and [[Link2]]."
        assert len(result.metadata["links"]) == 2

    def test_links_with_special_characters(self):
        """특수 문자를 포함한 링크를 파싱한다."""
        source = "See [[Special Link Name]] here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0] == "Special Link Name"

    def test_duplicate_links_removed(self):
        """중복 링크는 제거된다."""
        source = "[[Link1]] and [[Link1]] again."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0] == "Link1"

    def test_links_order_preserved(self):
        """링크의 순서가 유지된다."""
        source = "[[Alpha]], [[Beta]], [[Gamma]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["links"] == ["Alpha", "Beta", "Gamma"]

    def test_mixed_links_and_categories(self):
        """링크와 카테고리가 섞여 있을 때를 파싱한다."""
        source = "[[Category:Wiki]]\n\nContent with [[Link1]]."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Wiki"]
        assert result.metadata["links"] == ["Link1"]

    def test_complex_document_with_all_link_types(self):
        """모든 타입의 링크를 포함한 복잡한 문서를 파싱한다."""
        source = (
            "[[Category:Wiki]]\n"
            "[[Redirect:NewPage]]\n"
            "\n"
            "See [[Link1]] and [[Link2]] for details."
        )
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Wiki"]
        assert len(result.metadata["links"]) == 2
        assert "Link1" in result.metadata["links"]
        assert "Link2" in result.metadata["links"]
        assert "redirects" in result.metadata
        assert result.metadata["redirects"][0]["to"] == "NewPage"

    def test_parses_internal_link_with_label(self):
        """레이블이 있는 내부 링크를 파싱한다."""
        source = "See [[Document|this document]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0] == "Document"
        assert result.blocks[0]["content"] == "See [[Document|this document]] for details."

    def test_parses_multiple_links_with_labels(self):
        """여러 개의 레이블이 있는 내부 링크를 파싱한다."""
        source = "See [[Link1|first link]] and [[Link2|second link]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 2
        assert "Link1" in result.metadata["links"]
        assert "Link2" in result.metadata["links"]

    def test_parses_mixed_links_with_and_without_labels(self):
        """레이블이 있는 링크와 없는 링크를 섞어서 파싱한다."""
        source = "See [[Plain]] and [[Labeled|with label]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 2
        assert "Plain" in result.metadata["links"]
        assert "Labeled" in result.metadata["links"]
        assert result.blocks[0]["content"] == "See [[Plain]] and [[Labeled|with label]] for details."

    def test_link_with_label_preserves_label_in_content(self):
        """레이블은 블록 콘텐츠에 보존된다."""
        source = "Check [[WikiPage|our wiki]] now."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["content"] == "Check [[WikiPage|our wiki]] now."
        assert result.metadata["links"] == ["WikiPage"]


class TestPlainTextBlockParserHeadingsNestedLevels:
    """PlainTextBlockParser의 중첩된 제목 수준 파싱 테스트."""

    def test_parses_heading_level_two(self):
        """제목 수준 2를 파싱한다."""
        source = "== Section =="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 2
        assert result.blocks[0]["content"] == "Section"

    def test_parses_heading_level_three(self):
        """제목 수준 3을 파싱한다."""
        source = "=== Subsection ==="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 3
        assert result.blocks[0]["content"] == "Subsection"

    def test_parses_heading_level_four(self):
        """제목 수준 4를 파싱한다."""
        source = "==== Subsubsection ===="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 4
        assert result.blocks[0]["content"] == "Subsubsection"

    def test_parses_heading_level_five(self):
        """제목 수준 5를 파싱한다."""
        source = "===== Very Deep ====="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 5
        assert result.blocks[0]["content"] == "Very Deep"

    def test_parses_multiple_heading_levels_in_sequence(self):
        """여러 수준의 제목을 순서대로 파싱한다."""
        source = "= Level 1 =\n\n== Level 2 ==\n\n=== Level 3 ==="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["level"] == 1
        assert result.blocks[1]["level"] == 2
        assert result.blocks[2]["level"] == 3

    def test_heading_levels_in_metadata(self):
        """다양한 수준의 제목이 메타데이터에 포함된다."""
        source = "= Level 1 =\n\n== Level 2 ==\n\n=== Level 3 ==="
        result = PlainTextBlockParser.parse(source)
        headings = result.metadata["headings"]
        assert len(headings) == 3
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "Level 1"
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "Level 2"
        assert headings[2]["level"] == 3
        assert headings[2]["text"] == "Level 3"

    def test_nested_headings_with_content(self):
        """제목 사이에 콘텐츠가 있는 중첩된 제목을 파싱한다."""
        source = (
            "= Main =\n"
            "\n"
            "Main content.\n"
            "\n"
            "== Subsection ==\n"
            "\n"
            "Subsection content.\n"
            "\n"
            "=== Details ==="
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 5
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 1
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[2]["type"] == "heading"
        assert result.blocks[2]["level"] == 2
        assert result.blocks[3]["type"] == "paragraph"
        assert result.blocks[4]["type"] == "heading"
        assert result.blocks[4]["level"] == 3

    def test_heading_with_special_chars_multiple_levels(self):
        """특수 문자를 포함한 여러 수준의 제목을 파싱한다."""
        source = (
            "= Main: Chapter 1 & 2 =\n"
            "\n"
            "== Section 1.1 (Important) =="
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["content"] == "Main: Chapter 1 & 2"
        assert result.blocks[1]["content"] == "Section 1.1 (Important)"

    def test_mismatched_equal_signs_not_heading(self):
        """등호 기호 개수가 맞지 않으면 제목으로 취급하지 않는다."""
        source = "= Title =="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"

    def test_heading_level_extracted_from_equal_count(self):
        """제목 수준이 등호 기호 개수에서 올바르게 추출된다."""
        test_cases = [
            ("= One =", 1),
            ("== Two ==", 2),
            ("=== Three ===", 3),
            ("==== Four ====", 4),
            ("===== Five =====", 5),
            ("====== Six ======", 6),
        ]
        for source, expected_level in test_cases:
            result = PlainTextBlockParser.parse(source)
            assert len(result.blocks) == 1
            assert result.blocks[0]["level"] == expected_level, f"Failed for {source}"

    def test_heading_level_two_followed_by_content(self):
        """수준 2 제목 다음에 콘텐츠가 있는 경우를 파싱한다."""
        source = "== Title ==\n\nContent here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["level"] == 2
        assert result.blocks[0]["content"] == "Title"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Content here."

    def test_complex_document_with_multiple_levels(self):
        """여러 수준의 제목을 포함한 복잡한 문서를 파싱한다."""
        source = (
            "= Chapter 1 =\n"
            "\n"
            "Introduction.\n"
            "\n"
            "== Section 1.1 ==\n"
            "\n"
            "Content for 1.1.\n"
            "\n"
            "=== Subsection 1.1.1 ===\n"
            "\n"
            "Deep content.\n"
            "\n"
            "== Section 1.2 ==\n"
            "\n"
            "Content for 1.2."
        )
        result = PlainTextBlockParser.parse(source)
        headings = result.metadata["headings"]
        assert len(headings) == 4
        assert headings[0]["level"] == 1
        assert headings[1]["level"] == 2
        assert headings[2]["level"] == 3
        assert headings[3]["level"] == 2


class TestPlainTextBlockParserExternalLinks:
    """PlainTextBlockParser의 외부 링크 파싱 테스트."""

    def test_parses_single_external_link(self):
        """단일 외부 링크를 파싱한다."""
        source = "Visit [https://example.com] for more info."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com"

    def test_parses_multiple_external_links(self):
        """여러 외부 링크를 파싱한다."""
        source = "Check [https://site1.com] and [https://site2.com] now."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 2
        assert "https://site1.com" in result.metadata["external_links"]
        assert "https://site2.com" in result.metadata["external_links"]

    def test_external_link_with_label_space_separated(self):
        """공백으로 구분된 레이블이 있는 외부 링크를 파싱한다."""
        source = "Visit [https://example.com our site] for details."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com"

    def test_external_link_with_label_pipe_separated(self):
        """파이프로 구분된 레이블이 있는 외부 링크를 파싱한다."""
        source = "Visit [https://example.com|our site] for details."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com"

    def test_parses_http_external_links(self):
        """HTTP 프로토콜 외부 링크를 파싱한다."""
        source = "See [http://example.com] here."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "http://example.com"

    def test_parses_ftp_external_links(self):
        """FTP 프로토콜 외부 링크를 파싱한다."""
        source = "Download from [ftp://files.example.com]."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "ftp://files.example.com"

    def test_external_links_with_query_parameters(self):
        """쿼리 매개변수가 있는 외부 링크를 파싱한다."""
        source = "Search [https://example.com/search?q=test] now."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com/search?q=test"

    def test_external_links_with_fragment(self):
        """프래그먼트가 있는 외부 링크를 파싱한다."""
        source = "Go to [https://example.com/page#section] section."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com/page#section"

    def test_duplicate_external_links_removed(self):
        """중복 외부 링크는 제거된다."""
        source = "[https://example.com] and [https://example.com] again."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com"

    def test_external_links_order_preserved(self):
        """외부 링크의 순서가 유지된다."""
        source = "[https://alpha.com], [https://beta.com], [https://gamma.com]"
        result = PlainTextBlockParser.parse(source)
        assert "external_links" in result.metadata
        assert result.metadata["external_links"] == [
            "https://alpha.com",
            "https://beta.com",
            "https://gamma.com",
        ]

    def test_mixed_internal_and_external_links(self):
        """내부 링크와 외부 링크를 섞어서 파싱한다."""
        source = "See [[InternalLink]] and [https://example.com external] for info."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert "InternalLink" in result.metadata["links"]
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 1
        assert result.metadata["external_links"][0] == "https://example.com"

    def test_no_external_links_in_metadata_when_none_found(self):
        """외부 링크가 없을 때 메타데이터에 포함되지 않는다."""
        source = "This is plain text."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" not in result.metadata

    def test_external_links_preserved_in_content(self):
        """외부 링크는 블록 콘텐츠에 보존된다."""
        source = "Check [https://example.com our site] now."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["content"] == "Check [https://example.com our site] now."

    def test_external_links_in_multiple_blocks(self):
        """여러 블록의 외부 링크를 파싱한다."""
        source = "First [https://site1.com].\n\nSecond [https://site2.com]."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert "external_links" in result.metadata
        assert len(result.metadata["external_links"]) == 2
        assert "https://site1.com" in result.metadata["external_links"]
        assert "https://site2.com" in result.metadata["external_links"]

    def test_invalid_protocol_not_external_link(self):
        """유효하지 않은 프로토콜은 외부 링크로 취급하지 않는다."""
        source = "This [foobar://example.com] is not a valid link."
        result = PlainTextBlockParser.parse(source)
        assert "external_links" not in result.metadata or len(result.metadata.get("external_links", [])) == 0


class TestPlainTextBlockParserBoldText:
    """PlainTextBlockParser의 굵은 텍스트 파싱 테스트."""

    def test_parses_single_bold_text(self):
        """단일 굵은 텍스트를 파싱한다."""
        source = "This is '''bold text''' in a paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is '''bold text''' in a paragraph."

    def test_parses_bold_text_at_start(self):
        """문장 시작의 굳은 텍스트를 파싱한다."""
        source = "'''Bold''' text here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "'''Bold''' text here."

    def test_parses_bold_text_at_end(self):
        """문장 끝의 굵은 텍스트를 파싱한다."""
        source = "Text is '''bold'''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text is '''bold'''."

    def test_parses_multiple_bold_texts(self):
        """여러 개의 굵은 텍스트를 파싱한다."""
        source = "This has '''first bold''' and '''second bold''' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This has '''first bold''' and '''second bold''' text."

    def test_bold_text_with_special_characters(self):
        """특수 문자를 포함한 굵은 텍스트를 파싱한다."""
        source = "This is '''bold & important!''' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is '''bold & important!''' text."

    def test_bold_text_with_numbers(self):
        """숫자를 포함한 굵은 텍스트를 파싱한다."""
        source = "This is '''bold 123''' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is '''bold 123''' text."

    def test_bold_text_preserved_in_multiple_blocks(self):
        """여러 블록에서 굵은 텍스트가 보존된다."""
        source = "First '''bold''' paragraph.\n\nSecond '''bold''' paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert "'''bold'''" in result.blocks[0]["content"]
        assert "'''bold'''" in result.blocks[1]["content"]

    def test_bold_text_with_internal_whitespace(self):
        """내부 공백을 포함한 굵은 텍스트를 파싱한다."""
        source = "Text with '''multiple words in bold''' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with '''multiple words in bold''' here."

    def test_bold_text_adjacent_to_links(self):
        """링크 옆의 굵은 텍스트를 파싱한다."""
        source = "See '''bold''' and [[Link]] together."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "'''bold'''" in result.blocks[0]["content"]
        assert "[[Link]]" in result.blocks[0]["content"]

    def test_bold_text_does_not_create_escaped_html_flag(self):
        """굵은 텍스트는 이스케이프된 HTML 플래그를 생성하지 않는다."""
        source = "Text with '''bold''' only."
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]

    def test_bold_text_empty_not_parsed(self):
        """빈 굵은 텍스트는 파싱되지 않는다."""
        source = "Text with '''''' no content."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with '''''' no content."

    def test_bold_text_with_single_quotes_inside(self):
        """굵은 텍스트 안에 단일 따옴표를 포함한다."""
        source = "Text with '''it's bold''' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with '''it's bold''' here."


class TestPlainTextBlockParserItalicText:
    """PlainTextBlockParser의 이탤릭 텍스트 파싱 테스트."""

    def test_parses_single_italic_text(self):
        """단일 이탤릭 텍스트를 파싱한다."""
        source = "This is ''italic text'' in a paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is ''italic text'' in a paragraph."

    def test_parses_italic_text_at_start(self):
        """문장 시작의 이탤릭 텍스트를 파싱한다."""
        source = "''Italic'' text here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "''Italic'' text here."

    def test_parses_italic_text_at_end(self):
        """문장 끝의 이탤릭 텍스트를 파싱한다."""
        source = "Text is ''italic''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text is ''italic''."

    def test_parses_multiple_italic_texts(self):
        """여러 개의 이탤릭 텍스트를 파싱한다."""
        source = "This has ''first italic'' and ''second italic'' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This has ''first italic'' and ''second italic'' text."

    def test_italic_text_with_special_characters(self):
        """특수 문자를 포함한 이탤릭 텍스트를 파싱한다."""
        source = "This is ''italic & emphasized!'' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is ''italic & emphasized!'' text."

    def test_italic_text_with_numbers(self):
        """숫자를 포함한 이탤릭 텍스트를 파싱한다."""
        source = "This is ''italic 123'' text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is ''italic 123'' text."

    def test_italic_text_preserved_in_multiple_blocks(self):
        """여러 블록에서 이탤릭 텍스트가 보존된다."""
        source = "First ''italic'' paragraph.\n\nSecond ''italic'' paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert "''italic''" in result.blocks[0]["content"]
        assert "''italic''" in result.blocks[1]["content"]

    def test_italic_text_with_internal_whitespace(self):
        """내부 공백을 포함한 이탤릭 텍스트를 파싱한다."""
        source = "Text with ''multiple words in italic'' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with ''multiple words in italic'' here."

    def test_italic_text_adjacent_to_links(self):
        """링크 옆의 이탤릭 텍스트를 파싱한다."""
        source = "See ''italic'' and [[Link]] together."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "''italic''" in result.blocks[0]["content"]
        assert "[[Link]]" in result.blocks[0]["content"]

    def test_italic_text_does_not_create_escaped_html_flag(self):
        """이탤릭 텍스트는 이스케이프된 HTML 플래그를 생성하지 않는다."""
        source = "Text with ''italic'' only."
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]

    def test_italic_text_empty_not_parsed(self):
        """빈 이탤릭 텍스트는 파싱되지 않는다."""
        source = "Text with '''' no content."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with '''' no content."

    def test_bold_and_italic_together(self):
        """굵은 텍스트와 이탤릭 텍스트가 함께 있을 때를 파싱한다."""
        source = "Text with '''bold''' and ''italic'' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "'''bold'''" in result.blocks[0]["content"]
        assert "''italic''" in result.blocks[0]["content"]
