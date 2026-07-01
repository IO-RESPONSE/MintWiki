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


class TestPlainTextBlockParserStrikeText:
    """PlainTextBlockParser의 취소선 텍스트 파싱 테스트."""

    def test_parses_single_strike_text(self):
        """단일 취소선 텍스트를 파싱한다."""
        source = "This is ~~strikethrough text~~ in a paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is ~~strikethrough text~~ in a paragraph."

    def test_parses_strike_text_at_start(self):
        """문장 시작의 취소선 텍스트를 파싱한다."""
        source = "~~Strike~~ text here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "~~Strike~~ text here."

    def test_parses_strike_text_at_end(self):
        """문장 끝의 취소선 텍스트를 파싱한다."""
        source = "Text is ~~strike~~."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text is ~~strike~~."

    def test_parses_multiple_strike_texts(self):
        """여러 개의 취소선 텍스트를 파싱한다."""
        source = "This has ~~first strike~~ and ~~second strike~~ text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This has ~~first strike~~ and ~~second strike~~ text."

    def test_strike_text_with_special_characters(self):
        """특수 문자를 포함한 취소선 텍스트를 파싱한다."""
        source = "This is ~~strike & obsolete!~~ text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is ~~strike & obsolete!~~ text."

    def test_strike_text_with_numbers(self):
        """숫자를 포함한 취소선 텍스트를 파싱한다."""
        source = "This is ~~strike 123~~ text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is ~~strike 123~~ text."

    def test_strike_text_preserved_in_multiple_blocks(self):
        """여러 블록에서 취소선 텍스트가 보존된다."""
        source = "First ~~strike~~ paragraph.\n\nSecond ~~strike~~ paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert "~~strike~~" in result.blocks[0]["content"]
        assert "~~strike~~" in result.blocks[1]["content"]

    def test_strike_text_with_internal_whitespace(self):
        """내부 공백을 포함한 취소선 텍스트를 파싱한다."""
        source = "Text with ~~multiple words in strike~~ here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with ~~multiple words in strike~~ here."

    def test_strike_text_adjacent_to_links(self):
        """링크 옆의 취소선 텍스트를 파싱한다."""
        source = "See ~~strike~~ and [[Link]] together."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "~~strike~~" in result.blocks[0]["content"]
        assert "[[Link]]" in result.blocks[0]["content"]

    def test_strike_text_does_not_create_escaped_html_flag(self):
        """취소선 텍스트는 이스케이프된 HTML 플래그를 생성하지 않는다."""
        source = "Text with ~~strike~~ only."
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]

    def test_strike_text_empty_not_parsed(self):
        """빈 취소선 텍스트는 파싱되지 않는다."""
        source = "Text with ~~~~ no content."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with ~~~~ no content."

    def test_bold_italic_and_strike_together(self):
        """굵은 텍스트, 이탤릭, 취소선이 함께 있을 때를 파싱한다."""
        source = "Text with '''bold''', ''italic'' and ~~strike~~ here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "'''bold'''" in result.blocks[0]["content"]
        assert "''italic''" in result.blocks[0]["content"]
        assert "~~strike~~" in result.blocks[0]["content"]


class TestPlainTextBlockParserNestedInlineMarks:
    """PlainTextBlockParser의 중첩된 인라인 마크 파싱 테스트."""

    def test_parses_bold_with_nested_italic(self):
        """굵은 텍스트 안에 중첩된 이탤릭을 파싱한다."""
        source = "This is '''bold ''italic'' text''' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is '''bold ''italic'' text''' here."

    def test_parses_italic_with_nested_bold(self):
        """이탤릭 안에 중첩된 굵은 텍스트를 파싱한다."""
        source = "This is ''italic '''bold''' text'' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is ''italic '''bold''' text'' here."

    def test_parses_bold_with_nested_strike(self):
        """굵은 텍스트 안에 중첩된 취소선을 파싱한다."""
        source = "This is '''bold ~~strikethrough~~ text''' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is '''bold ~~strikethrough~~ text''' here."

    def test_parses_italic_with_nested_strike(self):
        """이탤릭 안에 중첩된 취소선을 파싱한다."""
        source = "This is ''italic ~~strikethrough~~ text'' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is ''italic ~~strikethrough~~ text'' here."

    def test_parses_multiple_nested_marks(self):
        """여러 개의 중첩된 마크를 파싱한다."""
        source = "Text with '''bold ''italic''' text and '''another ~~strike~~ bold'''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert "'''bold ''italic'''" in result.blocks[0]["content"]
        assert "'''another ~~strike~~ bold'''" in result.blocks[0]["content"]

    def test_deeply_nested_marks(self):
        """깊게 중첩된 마크를 파싱한다."""
        source = "Text with '''bold ''italic ~~strike~~ italic'' bold'''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text with '''bold ''italic ~~strike~~ italic'' bold'''."

    def test_nested_marks_with_special_characters(self):
        """특수 문자를 포함한 중첩된 마크를 파싱한다."""
        source = "This is '''bold & ''important!'' text''' here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "This is '''bold & ''important!'' text''' here."

    def test_nested_marks_at_paragraph_start(self):
        """문단 시작의 중첩된 마크를 파싱한다."""
        source = "'''Bold ''italic'' text''' continues here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "'''Bold ''italic'' text''' continues here."

    def test_nested_marks_at_paragraph_end(self):
        """문단 끝의 중첩된 마크를 파싱한다."""
        source = "Text ends with '''bold ''italic'' text'''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "Text ends with '''bold ''italic'' text'''."

    def test_nested_marks_in_multiple_blocks(self):
        """여러 블록의 중첩된 마크를 파싱한다."""
        source = "First '''bold ''italic'' text'''.\n\nSecond ''italic '''bold''' text''."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert "'''bold ''italic'' text'''" in result.blocks[0]["content"]
        assert "''italic '''bold''' text''" in result.blocks[1]["content"]

    def test_nested_marks_do_not_create_escaped_html_flag(self):
        """중첩된 마크는 이스케이프된 HTML 플래그를 생성하지 않는다."""
        source = "Text with '''bold ''italic'' text''' only."
        result = PlainTextBlockParser.parse(source)
        assert "has_escaped_html" not in result.blocks[0]


class TestPlainTextBlockParserUnorderedLists:
    """PlainTextBlockParser의 순서 없는 목록 파싱 테스트."""

    def test_parses_single_list_item(self):
        """단일 목록 항목을 파싱한다."""
        source = "* Item 1"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[0]["list_type"] == "unordered"
        assert len(result.blocks[0]["items"]) == 1
        assert result.blocks[0]["items"][0]["level"] == 1
        assert result.blocks[0]["items"][0]["text"] == "Item 1"

    def test_parses_multiple_list_items(self):
        """여러 목록 항목을 파싱한다."""
        source = "* Item 1\n* Item 2\n* Item 3"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 3
        assert result.blocks[0]["items"][0]["text"] == "Item 1"
        assert result.blocks[0]["items"][1]["text"] == "Item 2"
        assert result.blocks[0]["items"][2]["text"] == "Item 3"

    def test_parses_nested_list_items(self):
        """중첩된 목록 항목을 파싱한다."""
        source = "* Item 1\n** Nested 1.1\n** Nested 1.2\n* Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 2
        assert result.blocks[0]["items"][0]["level"] == 1
        assert len(result.blocks[0]["items"][0]["children"]) == 2
        assert result.blocks[0]["items"][0]["children"][0]["level"] == 2
        assert result.blocks[0]["items"][0]["children"][1]["level"] == 2
        assert result.blocks[0]["items"][1]["level"] == 1
        assert len(result.blocks[0]["items"][1]["children"]) == 0

    def test_list_followed_by_paragraph(self):
        """목록 다음에 문단이 있는 경우를 파싱한다."""
        source = "* Item 1\n* Item 2\n\nContent here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Content here."

    def test_paragraph_followed_by_list(self):
        """문단 다음에 목록이 있는 경우를 파싱한다."""
        source = "Content here.\n\n* Item 1\n* Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "list"

    def test_list_with_special_characters(self):
        """특수 문자를 포함한 목록 항목을 파싱한다."""
        source = "* Item with & special!\n* Item with 123 numbers"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with & special!"
        assert result.blocks[0]["items"][1]["text"] == "Item with 123 numbers"

    def test_deeply_nested_list(self):
        """깊게 중첩된 목록을 파싱한다."""
        source = "* Level 1\n** Level 2\n*** Level 3\n** Back to 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        items = result.blocks[0]["items"]
        assert items[0]["level"] == 1
        assert items[0]["children"][0]["level"] == 2
        assert items[0]["children"][0]["children"][0]["level"] == 3
        assert items[0]["children"][1]["level"] == 2

    def test_list_with_spaces_after_asterisk(self):
        """별표 뒤에 공백이 있는 목록을 파싱한다."""
        source = "*  Item with two spaces\n*   Item with three spaces"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with two spaces"
        assert result.blocks[0]["items"][1]["text"] == "Item with three spaces"

    def test_multiple_lists_separated_by_blank_lines(self):
        """빈 줄로 분리된 여러 목록을 파싱한다."""
        source = "* List 1 Item 1\n* List 1 Item 2\n\n* List 2 Item 1"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 2
        assert len(result.blocks[1]["items"]) == 1

    def test_list_with_internal_whitespace(self):
        """항목 내에 내부 공백을 포함한 목록을 파싱한다."""
        source = "* Item with multiple words inside\n* Another item with words"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with multiple words inside"

    def test_list_metadata_extraction(self):
        """목록 블록이 메타데이터에 영향을 주지 않는다."""
        source = "* Item [[Link1]]\n* Item [[Link2]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        # 목록 내의 링크는 메타데이터로 추출되지 않음 (현재 구현에서)
        assert len(result.metadata["links"]) == 0

    def test_heading_followed_by_list(self):
        """제목 다음에 목록이 오는 경우를 파싱한다."""
        source = "= Title =\n\n* Item 1\n* Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "list"


class TestPlainTextBlockParserOrderedLists:
    """PlainTextBlockParser의 순서 있는 목록 파싱 테스트."""

    def test_parses_single_list_item(self):
        """단일 목록 항목을 파싱한다."""
        source = "# Item 1"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[0]["list_type"] == "ordered"
        assert len(result.blocks[0]["items"]) == 1
        assert result.blocks[0]["items"][0]["level"] == 1
        assert result.blocks[0]["items"][0]["text"] == "Item 1"

    def test_parses_multiple_list_items(self):
        """여러 목록 항목을 파싱한다."""
        source = "# Item 1\n# Item 2\n# Item 3"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 3
        assert result.blocks[0]["items"][0]["text"] == "Item 1"
        assert result.blocks[0]["items"][1]["text"] == "Item 2"
        assert result.blocks[0]["items"][2]["text"] == "Item 3"

    def test_parses_nested_list_items(self):
        """중첩된 목록 항목을 파싱한다."""
        source = "# Item 1\n## Nested 1.1\n## Nested 1.2\n# Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 2
        assert result.blocks[0]["items"][0]["level"] == 1
        assert len(result.blocks[0]["items"][0]["children"]) == 2
        assert result.blocks[0]["items"][0]["children"][0]["level"] == 2
        assert result.blocks[0]["items"][0]["children"][1]["level"] == 2
        assert result.blocks[0]["items"][1]["level"] == 1
        assert len(result.blocks[0]["items"][1]["children"]) == 0

    def test_list_followed_by_paragraph(self):
        """목록 다음에 문단이 있는 경우를 파싱한다."""
        source = "# Item 1\n# Item 2\n\nContent here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Content here."

    def test_paragraph_followed_by_list(self):
        """문단 다음에 목록이 있는 경우를 파싱한다."""
        source = "Content here.\n\n# Item 1\n# Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "list"

    def test_list_with_special_characters(self):
        """특수 문자를 포함한 목록 항목을 파싱한다."""
        source = "# Item with & special!\n# Item with 123 numbers"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with & special!"
        assert result.blocks[0]["items"][1]["text"] == "Item with 123 numbers"

    def test_deeply_nested_list(self):
        """깊게 중첩된 목록을 파싱한다."""
        source = "# Level 1\n## Level 2\n### Level 3\n## Back to 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        items = result.blocks[0]["items"]
        assert items[0]["level"] == 1
        assert items[0]["children"][0]["level"] == 2
        assert items[0]["children"][0]["children"][0]["level"] == 3
        assert items[0]["children"][1]["level"] == 2

    def test_list_with_spaces_after_hash(self):
        """해시 뒤에 공백이 있는 목록을 파싱한다."""
        source = "#  Item with two spaces\n#   Item with three spaces"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with two spaces"
        assert result.blocks[0]["items"][1]["text"] == "Item with three spaces"

    def test_multiple_lists_separated_by_blank_lines(self):
        """빈 줄로 분리된 여러 목록을 파싱한다."""
        source = "# List 1 Item 1\n# List 1 Item 2\n\n# List 2 Item 1"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "list"
        assert len(result.blocks[0]["items"]) == 2
        assert len(result.blocks[1]["items"]) == 1

    def test_list_with_internal_whitespace(self):
        """항목 내에 내부 공백을 포함한 목록을 파싱한다."""
        source = "# Item with multiple words inside\n# Another item with words"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["items"][0]["text"] == "Item with multiple words inside"

    def test_heading_followed_by_ordered_list(self):
        """제목 다음에 순서 있는 목록이 오는 경우를 파싱한다."""
        source = "= Title =\n\n# Item 1\n# Item 2"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "list"
        assert result.blocks[1]["list_type"] == "ordered"

    def test_ordered_and_unordered_lists_separate(self):
        """순서 있는 목록과 순서 없는 목록이 분리되어 있는 경우를 파싱한다."""
        source = "# Item 1\n# Item 2\n\n* Item A\n* Item B"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["list_type"] == "ordered"
        assert result.blocks[1]["list_type"] == "unordered"


class TestPlainTextBlockParserHorizontalRule:
    """수평선 파싱 테스트."""

    def test_parses_horizontal_rule_simple(self):
        """간단한 수평선을 파싱한다."""
        source = "----"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "horizontal_rule"

    def test_parses_horizontal_rule_with_text(self):
        """텍스트와 함께 있는 수평선을 파싱한다."""
        source = "= Title =\n\nContent here.\n\n----\n\nMore content."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 4
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[2]["type"] == "horizontal_rule"
        assert result.blocks[3]["type"] == "paragraph"

    def test_parses_horizontal_rule_multiple(self):
        """여러 개의 수평선을 파싱한다."""
        source = "----\n\n----\n\n-----"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert all(block["type"] == "horizontal_rule" for block in result.blocks)

    def test_parses_horizontal_rule_with_more_dashes(self):
        """4개보다 많은 대시로 이루어진 수평선을 파싱한다."""
        source = "----------"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "horizontal_rule"

    def test_horizontal_rule_not_parsed_with_less_than_four_dashes(self):
        """4개 미만의 대시는 수평선이 아니다."""
        source = "---"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "---"

    def test_horizontal_rule_with_leading_spaces(self):
        """앞에 공백이 있는 수평선을 파싱한다."""
        source = "  ----"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "horizontal_rule"

    def test_horizontal_rule_with_trailing_spaces(self):
        """뒤에 공백이 있는 수평선을 파싱한다."""
        source = "----  "
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "horizontal_rule"

    def test_horizontal_rule_between_paragraphs(self):
        """문단 사이의 수평선을 파싱한다."""
        source = "First paragraph.\n\n----\n\nSecond paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "horizontal_rule"
        assert result.blocks[2]["type"] == "paragraph"

    def test_horizontal_rule_after_heading(self):
        """제목 다음의 수평선을 파싱한다."""
        source = "= Title =\n\n----"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "horizontal_rule"


class TestPlainTextBlockParserLineBreak:
    """줄 바꿈 매크로 파싱 테스트."""

    def test_parses_line_break_simple(self):
        """간단한 줄 바꿈을 파싱한다."""
        source = "\\\\"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "line_break"

    def test_parses_line_break_with_text(self):
        """텍스트와 함께 있는 줄 바꿈을 파싱한다."""
        source = "First line.\n\n\\\\\n\nSecond line."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "First line."
        assert result.blocks[1]["type"] == "line_break"
        assert result.blocks[2]["type"] == "paragraph"
        assert result.blocks[2]["content"] == "Second line."

    def test_parses_multiple_line_breaks(self):
        """여러 개의 줄 바꿈을 파싱한다."""
        source = "\\\\\n\n\\\\\n\n\\\\"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert all(block["type"] == "line_break" for block in result.blocks)

    def test_line_break_between_paragraphs(self):
        """문단 사이의 줄 바꿈을 파싱한다."""
        source = "First paragraph.\n\n\\\\\n\nSecond paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "line_break"
        assert result.blocks[2]["type"] == "paragraph"

    def test_line_break_after_heading(self):
        """제목 다음의 줄 바꿈을 파싱한다."""
        source = "= Title =\n\n\\\\"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "line_break"

    def test_line_break_before_heading(self):
        """줄 바꿈 다음의 제목을 파싱한다."""
        source = "\\\\\n\n= Title ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "line_break"
        assert result.blocks[1]["type"] == "heading"

    def test_line_break_with_list(self):
        """목록과 함께 있는 줄 바꿈을 파싱한다."""
        source = "* Item 1\n* Item 2\n\n\\\\\n\n* Item 3"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "line_break"
        assert result.blocks[2]["type"] == "list"

    def test_line_break_with_horizontal_rule(self):
        """수평선과 함께 있는 줄 바꿈을 파싱한다."""
        source = "----\n\n\\\\\n\n----"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "horizontal_rule"
        assert result.blocks[1]["type"] == "line_break"
        assert result.blocks[2]["type"] == "horizontal_rule"

    def test_line_break_not_created_with_text_before_backslashes(self):
        """백슬래시 앞에 텍스트가 있으면 줄 바꿈이 아니다."""
        source = "text\\\\"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "text\\\\"

    def test_line_break_metadata_extraction(self):
        """줄 바꿈 블록이 메타데이터에 영향을 주지 않는다."""
        source = "Text [[Link]].\n\n\\\\\n\nMore text."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0] == "Link"

    def test_complex_document_with_line_breaks(self):
        """줄 바꿈을 포함한 복잡한 문서를 파싱한다."""
        source = (
            "= Title =\n"
            "\n"
            "Introduction.\n"
            "\n"
            "\\\\\n"
            "\n"
            "More content.\n"
            "\n"
            "----\n"
            "\n"
            "Final paragraph."
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 6
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[2]["type"] == "line_break"
        assert result.blocks[3]["type"] == "paragraph"
        assert result.blocks[4]["type"] == "horizontal_rule"
        assert result.blocks[5]["type"] == "paragraph"


class TestPlainTextBlockParserNowiki:
    """PlainTextBlockParser의 nowiki 블록 파싱 테스트."""

    def test_parses_simple_nowiki_block(self):
        """단순 nowiki 블록을 파싱한다."""
        source = "<nowiki>'''bold'''</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "'''bold'''"

    def test_parses_nowiki_with_wiki_markup(self):
        """위키 마크업을 포함한 nowiki 블록을 파싱한다."""
        source = "<nowiki>[[Link]] and '''bold''' and ''italic''</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "[[Link]] and '''bold''' and ''italic''"

    def test_parses_nowiki_multiline(self):
        """여러 줄의 nowiki 블록을 파싱한다."""
        source = "<nowiki>\nFirst line\nSecond line\n</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "First line\nSecond line"

    def test_parses_nowiki_with_text_before_and_after(self):
        """텍스트와 함께 있는 nowiki 블록을 파싱한다."""
        source = "This is a paragraph.\n\n<nowiki>'''bold'''</nowiki>\n\nAnother paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is a paragraph."
        assert result.blocks[1]["type"] == "nowiki"
        assert result.blocks[1]["content"] == "'''bold'''"
        assert result.blocks[2]["type"] == "paragraph"
        assert result.blocks[2]["content"] == "Another paragraph."

    def test_parses_nowiki_with_special_characters(self):
        """특수 문자를 포함한 nowiki 블록을 파싱한다."""
        source = "<nowiki>< > & ' \" [[ ]] {{ }}</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "< > & ' \" [[ ]] {{ }}"

    def test_parses_multiple_nowiki_blocks(self):
        """여러 개의 nowiki 블록을 파싱한다."""
        source = "<nowiki>First block</nowiki>\n\n<nowiki>Second block</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "First block"
        assert result.blocks[1]["type"] == "nowiki"
        assert result.blocks[1]["content"] == "Second block"

    def test_parses_nowiki_with_heading(self):
        """제목과 함께 있는 nowiki 블록을 파싱한다."""
        source = "= Title =\n\n<nowiki>'''bold'''</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[0]["content"] == "Title"
        assert result.blocks[1]["type"] == "nowiki"
        assert result.blocks[1]["content"] == "'''bold'''"

    def test_parses_nowiki_with_list(self):
        """목록과 함께 있는 nowiki 블록을 파싱한다."""
        source = "* Item 1\n* Item 2\n\n<nowiki>* Not a list</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "nowiki"
        assert result.blocks[1]["content"] == "* Not a list"

    def test_parses_nowiki_with_horizontal_rule(self):
        """수평선과 함께 있는 nowiki 블록을 파싱한다."""
        source = "----\n\n<nowiki>----</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "horizontal_rule"
        assert result.blocks[1]["type"] == "nowiki"
        assert result.blocks[1]["content"] == "----"

    def test_nowiki_does_not_extract_metadata(self):
        """nowiki 블록의 내용은 메타데이터로 추출되지 않는다."""
        source = "<nowiki>[[Link]] and [[Category:Test]]</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["links"]) == 0
        assert len(result.metadata["categories"]) == 0

    def test_nowiki_with_html_entities(self):
        """HTML 엔티티를 포함한 nowiki 블록을 파싱한다."""
        source = "<nowiki>&lt;tag&gt; and &amp;</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "&lt;tag&gt; and &amp;"

    def test_nowiki_single_line_with_content(self):
        """한 줄 내에 모든 콘텐츠가 있는 nowiki 블록을 파싱한다."""
        source = "<nowiki>some content</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["content"] == "some content"

    def test_nowiki_empty_block(self):
        """빈 nowiki 블록을 파싱한다."""
        source = "<nowiki></nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == ""

    def test_nowiki_case_insensitive(self):
        """대소문자를 무시하는 nowiki 태그를 파싱한다."""
        source = "<NOWIKI>content</NOWIKI>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "content"

    def test_nowiki_mixed_case(self):
        """혼합 대소문자의 nowiki 태그를 파싱한다."""
        source = "<NoWiki>content</noWIKI>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "content"

    def test_nowiki_with_trailing_content_on_same_line(self):
        """닫는 태그 이후 같은 줄에 콘텐츠가 있는 경우를 파싱한다."""
        source = "<nowiki>content</nowiki> extra text"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "nowiki"
        assert result.blocks[0]["content"] == "content"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == " extra text"

    def test_nowiki_spanning_many_lines(self):
        """많은 줄에 걸쳐 있는 nowiki 블록을 파싱한다."""
        source = "<nowiki>\nline1\nline2\nline3\nline4\n</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "nowiki"
        assert "line1" in result.blocks[0]["content"]
        assert "line4" in result.blocks[0]["content"]

    def test_nowiki_preserves_exact_content(self):
        """nowiki 블록이 정확한 콘텐츠를 보존한다."""
        source = "<nowiki>  spaces  and\ttabs\t</nowiki>"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["content"] == "  spaces  and\ttabs\t"

    def test_multiple_blocks_complex(self):
        """복잡한 다양한 블록들을 파싱한다."""
        source = (
            "= Header =\n"
            "\n"
            "Text paragraph.\n"
            "\n"
            "<nowiki>'''not bold'''</nowiki>\n"
            "\n"
            "* List item\n"
            "\n"
            "<nowiki>* not a list</nowiki>"
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 5
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[2]["type"] == "nowiki"
        assert result.blocks[3]["type"] == "list"
        assert result.blocks[4]["type"] == "nowiki"


class TestPlainTextBlockParserCode:
    """코드 블록 파서 테스트."""

    def test_parses_simple_code_block(self):
        """단순 코드 블록을 파싱한다."""
        source = "{{{x = 10}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "x = 10"

    def test_parses_code_with_syntax(self):
        """프로그래밍 문법을 포함한 코드 블록을 파싱한다."""
        source = "{{{def foo():\n    return 42}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert "def foo():" in result.blocks[0]["content"]
        assert "return 42" in result.blocks[0]["content"]

    def test_parses_code_multiline(self):
        """여러 줄의 코드 블록을 파싱한다."""
        source = "{{{\nFirst line\nSecond line\n}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "First line\nSecond line"

    def test_parses_code_with_text_before_and_after(self):
        """텍스트 전후의 코드 블록을 파싱한다."""
        source = "This is a paragraph.\n\n{{{x = 10}}}\n\nAnother paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 3
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "This is a paragraph."
        assert result.blocks[1]["type"] == "code"
        assert result.blocks[1]["content"] == "x = 10"
        assert result.blocks[2]["type"] == "paragraph"
        assert result.blocks[2]["content"] == "Another paragraph."

    def test_parses_code_with_special_characters(self):
        """특수 문자를 포함한 코드 블록을 파싱한다."""
        source = "{{{& < > ' \" [ ] {{ # ! ~}}}"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "& < > ' \" [ ] {{ # ! ~"

    def test_parses_multiple_code_blocks(self):
        """여러 개의 코드 블록을 파싱한다."""
        source = "{{{First block}}}\n\n{{{Second block}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "First block"
        assert result.blocks[1]["type"] == "code"
        assert result.blocks[1]["content"] == "Second block"

    def test_code_with_heading(self):
        """제목과 함께 있는 코드 블록을 파싱한다."""
        source = "= Title =\n\n{{{code}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "code"

    def test_code_with_list(self):
        """목록과 함께 있는 코드 블록을 파싱한다."""
        source = "* Item\n\n{{{code}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "list"
        assert result.blocks[1]["type"] == "code"

    def test_code_does_not_extract_metadata(self):
        """코드 블록은 메타데이터를 추출하지 않는다."""
        source = "{{{[[Link]] and [[Category:Test]]}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert result.metadata["links"] == []
        assert result.metadata["categories"] == []

    def test_code_with_html_entities(self):
        """HTML 엔티티를 포함한 코드 블록을 파싱한다."""
        source = "{{{&lt;tag&gt; &amp; entity}}}"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["content"] == "&lt;tag&gt; &amp; entity"

    def test_code_empty_block(self):
        """빈 코드 블록을 파싱한다."""
        source = "{{{}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == ""

    def test_code_single_line_with_content(self):
        """한 줄 내에 완전한 코드 블록을 파싱한다."""
        source = "{{{int x = 5;}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "int x = 5;"

    def test_code_spanning_many_lines(self):
        """많은 줄에 걸쳐 있는 코드 블록을 파싱한다."""
        source = "{{{\nline1\nline2\nline3\nline4\n}}}"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "code"
        assert "line1" in result.blocks[0]["content"]
        assert "line4" in result.blocks[0]["content"]

    def test_code_preserves_exact_content(self):
        """코드 블록이 정확한 콘텐츠를 보존한다."""
        source = "{{{  spaces  and\ttabs\t}}}"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["content"] == "  spaces  and\ttabs\t"

    def test_code_with_trailing_content_on_same_line(self):
        """닫는 태그 이후 같은 줄에 콘텐츠가 있는 경우를 파싱한다."""
        source = "{{{content}}} extra text"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "code"
        assert result.blocks[0]["content"] == "content"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == " extra text"

    def test_multiple_blocks_with_code(self):
        """코드와 다른 블록 타입들의 복합을 파싱한다."""
        source = (
            "= Header =\n"
            "\n"
            "Text paragraph.\n"
            "\n"
            "{{{code block}}}\n"
            "\n"
            "* List item\n"
            "\n"
            "{{{another code}}}"
        )
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 5
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[2]["type"] == "code"
        assert result.blocks[3]["type"] == "list"
        assert result.blocks[4]["type"] == "code"


class TestPlainTextBlockParserRedirect:
    """리다이렉트 파싱 테스트."""

    def test_parses_simple_redirect(self):
        """단순 리다이렉트를 파싱한다."""
        source = "[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert len(result.metadata["redirects"]) == 1
        assert result.metadata["redirects"][0]["to"] == "NewPage"

    def test_redirect_with_from_field(self):
        """리다이렉트에 "from" 필드가 있다."""
        source = "[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert "from" in result.metadata["redirects"][0]

    def test_redirect_does_not_create_block(self):
        """리다이렉트는 블록을 생성하지 않는다."""
        source = "[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 0

    def test_redirect_with_main_heading(self):
        """메인 제목이 있을 때 리다이렉트의 "from" 필드가 설정된다."""
        source = "= Main Title =\n\n[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert result.metadata["redirects"][0]["from"] == "Main Title"
        assert result.metadata["redirects"][0]["to"] == "NewPage"

    def test_redirect_at_top_of_document(self):
        """문서 상단의 리다이렉트를 파싱한다."""
        source = "[[Redirect:TargetPage]]\n\n= Title =\n\nContent."
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert result.metadata["redirects"][0]["to"] == "TargetPage"
        assert result.metadata["redirects"][0]["from"] == "Title"

    def test_multiple_redirects(self):
        """여러 개의 리다이렉트를 파싱한다."""
        source = "= Page A =\n\n[[Redirect:NewPage]]\n\nContent with [[Redirect:Another]]."
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert len(result.metadata["redirects"]) == 2

    def test_redirect_with_category(self):
        """카테고리와 함께 있는 리다이렉트를 파싱한다."""
        source = "[[Category:Test]]\n[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Test"]
        assert len(result.metadata["redirects"]) == 1
        assert result.metadata["redirects"][0]["to"] == "NewPage"

    def test_redirect_does_not_appear_in_blocks(self):
        """리다이렉트 라인이 블록에 나타나지 않는다."""
        source = "[[Redirect:NewPage]]\n\nContent here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[0]["content"] == "Content here."

    def test_redirect_with_multiple_headings(self):
        """여러 제목이 있을 때 첫 번째 레벨 1 제목이 "from"으로 사용된다."""
        source = "= First Heading =\n\n[[Redirect:Target]]\n\n== Subsection =="
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["redirects"][0]["from"] == "First Heading"

    def test_redirect_in_paragraph_content(self):
        """문단 내의 리다이렉트를 파싱한다."""
        source = "= Title =\n\nSee [[Redirect:Other]] for details."
        result = PlainTextBlockParser.parse(source)
        assert "redirects" in result.metadata
        assert any(r["to"] == "Other" for r in result.metadata["redirects"])

    def test_redirect_preserves_main_heading(self):
        """리다이렉트는 메인 제목을 유지한다."""
        source = "= Main =\n\n[[Redirect:Target]]"
        result = PlainTextBlockParser.parse(source)
        headings = result.metadata["headings"]
        assert len(headings) == 1
        assert headings[0]["text"] == "Main"

    def test_redirect_target_with_spaces(self):
        """공백이 포함된 리다이렉트 대상을 파싱한다."""
        source = "= Title =\n\n[[Redirect:Target Page Name]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["redirects"][0]["to"] == "Target Page Name"

    def test_redirect_with_special_characters(self):
        """특수 문자가 포함된 리다이렉트를 파싱한다."""
        source = "= Main =\n\n[[Redirect:Target: Part 1 & Part 2]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["redirects"][0]["to"] == "Target: Part 1 & Part 2"

    def test_complex_document_with_redirect(self):
        """리다이렉트를 포함한 복잡한 문서를 파싱한다."""
        source = (
            "[[Category:Wiki]]\n"
            "[[Redirect:NewPage]]\n"
            "= Main Title =\n"
            "\n"
            "Introduction.\n"
            "\n"
            "== Section ==\n"
            "\n"
            "More content [[Link1]]."
        )
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Wiki"]
        assert result.metadata["redirects"][0]["from"] == "Main Title"
        assert result.metadata["redirects"][0]["to"] == "NewPage"
        assert "Link1" in result.metadata["links"]


class TestPlainTextBlockParserCategories:
    """카테고리 추출 파싱 테스트."""

    def test_parses_single_category(self):
        """단일 카테고리를 파싱한다."""
        source = "[[Category:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Test"

    def test_parses_multiple_categories(self):
        """여러 카테고리를 파싱한다."""
        source = "[[Category:Wiki]]\n[[Category:Technology]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 2
        assert "Wiki" in result.metadata["categories"]
        assert "Technology" in result.metadata["categories"]

    def test_categories_do_not_create_blocks(self):
        """카테고리는 블록을 생성하지 않는다."""
        source = "[[Category:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 0

    def test_categories_with_heading(self):
        """제목이 있는 카테고리를 파싱한다."""
        source = "[[Category:Documentation]]\n\n= Main Article ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Documentation"
        assert len(result.metadata["headings"]) == 1

    def test_categories_with_content(self):
        """콘텐츠와 함께 있는 카테고리를 파싱한다."""
        source = "[[Category:Tutorial]]\n\nSome content here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Tutorial"
        assert len(result.blocks) == 1

    def test_categories_with_multiple_content_blocks(self):
        """여러 콘텐츠 블록이 있는 카테고리를 파싱한다."""
        source = "[[Category:Guide]]\n\nFirst paragraph.\n\nSecond paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Guide"
        assert len(result.blocks) == 2

    def test_categories_order_preserved(self):
        """카테고리의 순서가 유지된다."""
        source = "[[Category:Alpha]]\n[[Category:Beta]]\n[[Category:Gamma]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Alpha", "Beta", "Gamma"]

    def test_duplicate_categories_removed(self):
        """중복 카테고리는 제거된다."""
        source = "[[Category:Test]]\n\nContent.\n\n[[Category:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["categories"]) == 1
        assert result.metadata["categories"][0] == "Test"

    def test_categories_with_special_characters(self):
        """특수 문자를 포함한 카테고리를 파싱한다."""
        source = "[[Category:Science & Technology]]\n[[Category:2024 Events]]"
        result = PlainTextBlockParser.parse(source)
        assert "Science & Technology" in result.metadata["categories"]
        assert "2024 Events" in result.metadata["categories"]

    def test_categories_with_numbers(self):
        """숫자를 포함한 카테고리를 파싱한다."""
        source = "[[Category:Level1]]\n[[Category:Chapter 2.5]]"
        result = PlainTextBlockParser.parse(source)
        assert "Level1" in result.metadata["categories"]
        assert "Chapter 2.5" in result.metadata["categories"]

    def test_categories_with_spaces(self):
        """공백을 포함한 카테고리를 파싱한다."""
        source = "[[Category:Multi Word Category]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Multi Word Category"]

    def test_categories_in_paragraph_content(self):
        """문단 콘텐츠 내의 카테고리를 파싱한다."""
        source = "= Title =\n\nSee [[Category:Reference]] for details."
        result = PlainTextBlockParser.parse(source)
        assert "Reference" in result.metadata["categories"]

    def test_categories_with_links(self):
        """링크와 함께 있는 카테고리를 파싱한다."""
        source = "[[Category:Wiki]]\n\nSee [[Document1]] for more."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Wiki"]
        assert "Document1" in result.metadata["links"]

    def test_categories_with_redirects(self):
        """리다이렉트와 함께 있는 카테고리를 파싱한다."""
        source = "[[Category:Archived]]\n[[Redirect:NewPage]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Archived"]
        assert "redirects" in result.metadata

    def test_categories_at_top_of_document(self):
        """문서 상단의 카테고리를 파싱한다."""
        source = "[[Category:Featured]]\n\n= Main =\n\nContent."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Featured"]
        assert len(result.blocks) == 2

    def test_categories_between_content(self):
        """콘텐츠 사이의 카테고리를 파싱한다."""
        source = "First paragraph.\n\n[[Category:Mixed]]\n\nSecond paragraph."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == ["Mixed"]
        assert len(result.blocks) == 2

    def test_empty_categories_list_when_none_found(self):
        """카테고리가 없을 때 빈 리스트를 반환한다."""
        source = "Just a paragraph."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["categories"] == []

    def test_categories_metadata_extraction(self):
        """카테고리 메타데이터를 올바르게 추출한다."""
        source = "[[Category:Test]]\n\nContent."
        result = PlainTextBlockParser.parse(source)
        assert "categories" in result.metadata
        assert isinstance(result.metadata["categories"], list)
        assert all(isinstance(c, str) for c in result.metadata["categories"])


class TestPlainTextBlockParserBacklinks:
    """백링크 추출 파싱 테스트."""

    def test_parses_single_backlink(self):
        """단일 백링크를 파싱한다."""
        source = "[[Backlink:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Test"

    def test_parses_multiple_backlinks(self):
        """여러 백링크를 파싱한다."""
        source = "[[Backlink:Page1]]\n[[Backlink:Page2]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 2
        assert "Page1" in result.metadata["backlinks"]
        assert "Page2" in result.metadata["backlinks"]

    def test_backlinks_do_not_create_blocks(self):
        """백링크는 블록을 생성하지 않는다."""
        source = "[[Backlink:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 0

    def test_backlinks_with_heading(self):
        """제목이 있는 백링크를 파싱한다."""
        source = "[[Backlink:Documentation]]\n\n= Main Article ="
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Documentation"
        assert len(result.metadata["headings"]) == 1

    def test_backlinks_with_content(self):
        """콘텐츠와 함께 있는 백링크를 파싱한다."""
        source = "[[Backlink:Tutorial]]\n\nSome content here."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Tutorial"
        assert len(result.blocks) == 1

    def test_backlinks_order_preserved(self):
        """백링크의 순서가 유지된다."""
        source = "[[Backlink:Alpha]]\n[[Backlink:Beta]]\n[[Backlink:Gamma]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["backlinks"] == ["Alpha", "Beta", "Gamma"]

    def test_duplicate_backlinks_removed(self):
        """중복 백링크는 제거된다."""
        source = "[[Backlink:Test]]\n\nContent.\n\n[[Backlink:Test]]"
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Test"

    def test_backlinks_with_special_characters(self):
        """특수 문자를 포함한 백링크를 파싱한다."""
        source = "[[Backlink:Science & Technology]]\n[[Backlink:2024 Events]]"
        result = PlainTextBlockParser.parse(source)
        assert "Science & Technology" in result.metadata["backlinks"]
        assert "2024 Events" in result.metadata["backlinks"]

    def test_backlinks_with_spaces(self):
        """공백을 포함한 백링크를 파싱한다."""
        source = "[[Backlink:Multi Word Backlink]]"
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["backlinks"] == ["Multi Word Backlink"]

    def test_backlinks_in_paragraph_content(self):
        """문단 콘텐츠 내의 백링크를 파싱한다."""
        source = "= Title =\n\nSee [[Backlink:Reference]] for details."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Reference"

    def test_empty_backlinks_list_when_none_found(self):
        """백링크가 없을 때 메타데이터에 포함되지 않는다."""
        source = "Just a paragraph."
        result = PlainTextBlockParser.parse(source)
        assert "backlinks" not in result.metadata

    def test_backlinks_at_top_of_document(self):
        """문서 상단의 백링크를 파싱한다."""
        source = "[[Backlink:Featured]]\n\n= Main =\n\nContent."
        result = PlainTextBlockParser.parse(source)
        assert result.metadata["backlinks"] == ["Featured"]
        assert len(result.blocks) == 2

    def test_backlinks_with_multiple_content_blocks(self):
        """여러 콘텐츠 블록이 있는 백링크를 파싱한다."""
        source = "[[Backlink:Guide]]\n\nFirst paragraph.\n\nSecond paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.metadata["backlinks"]) == 1
        assert result.metadata["backlinks"][0] == "Guide"
        assert len(result.blocks) == 2

    def test_backlinks_metadata_extraction(self):
        """백링크 메타데이터를 올바르게 추출한다."""
        source = "[[Backlink:Test]]\n\nContent."
        result = PlainTextBlockParser.parse(source)
        assert "backlinks" in result.metadata
        assert isinstance(result.metadata["backlinks"], list)
        assert all(isinstance(b, str) for b in result.metadata["backlinks"])


class TestPlainTextBlockParserSimpleTableRows:
    """PlainTextBlockParser의 간단한 테이블 행 파싱 테스트."""

    def test_parses_single_table_row(self):
        """단일 테이블 행을 파싱한다."""
        source = "||cell1||cell2||cell3||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "table"
        assert len(result.blocks[0]["rows"]) == 1
        assert result.blocks[0]["rows"][0]["type"] == "data"
        assert result.blocks[0]["rows"][0]["cells"] == ["cell1", "cell2", "cell3"]

    def test_parses_multiple_table_rows(self):
        """여러 테이블 행을 파싱한다."""
        source = "||row1cell1||row1cell2||\n||row2cell1||row2cell2||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "table"
        assert len(result.blocks[0]["rows"]) == 2
        assert result.blocks[0]["rows"][0]["type"] == "data"
        assert result.blocks[0]["rows"][0]["cells"] == ["row1cell1", "row1cell2"]
        assert result.blocks[0]["rows"][1]["type"] == "data"
        assert result.blocks[0]["rows"][1]["cells"] == ["row2cell1", "row2cell2"]

    def test_parses_table_with_heading(self):
        """테이블과 제목을 함께 파싱한다."""
        source = "= Table Title =\n\n||cell1||cell2||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "table"

    def test_parses_table_with_content(self):
        """테이블과 문단을 함께 파싱한다."""
        source = "Introductory text.\n\n||data1||data2||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "table"

    def test_table_cells_trimmed(self):
        """테이블 셀의 공백을 제거한다."""
        source = "||  cell1  ||  cell2  ||"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["rows"][0]["cells"] == ["cell1", "cell2"]

    def test_table_with_many_cells(self):
        """많은 셀을 가진 테이블 행을 파싱한다."""
        source = "||a||b||c||d||e||f||g||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks[0]["rows"][0]["cells"]) == 7

    def test_table_separated_from_paragraph_by_blank_line(self):
        """빈 줄로 분리된 테이블과 문단을 파싱한다."""
        source = "First paragraph.\n\n||cell1||cell2||\n||cell3||cell4||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "table"
        assert len(result.blocks[1]["rows"]) == 2

    def test_table_followed_by_paragraph(self):
        """테이블 뒤의 문단을 파싱한다."""
        source = "||cell1||cell2||\n\nFollowing paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "table"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Following paragraph."

    def test_consecutive_table_rows_grouped(self):
        """연속된 테이블 행을 하나의 블록으로 그룹화한다."""
        source = "||a||b||\n||c||d||\n||e||f||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "table"
        assert len(result.blocks[0]["rows"]) == 3

    def test_table_with_numeric_content(self):
        """숫자 콘텐츠를 포함한 테이블을 파싱한다."""
        source = "||1||2||3||\n||10||20||30||"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["rows"][0]["cells"] == ["1", "2", "3"]
        assert result.blocks[0]["rows"][1]["cells"] == ["10", "20", "30"]

    def test_table_not_created_from_non_table_content(self):
        """테이블이 아닌 콘텐츠는 테이블로 파싱되지 않는다."""
        source = "This is a paragraph with ||pipes||."
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["type"] == "paragraph"
        assert "table" not in [b["type"] for b in result.blocks]

    def test_table_row_structure_integrity(self):
        """테이블 행 구조의 무결성을 검증한다."""
        source = "||cell1||cell2||cell3||"
        result = PlainTextBlockParser.parse(source)
        table_block = result.blocks[0]
        assert "type" in table_block
        assert "rows" in table_block
        assert isinstance(table_block["rows"], list)
        assert all("cells" in row for row in table_block["rows"])

    def test_empty_table_cell_content(self):
        """빈 테이블 셀을 처리한다."""
        source = "||cell1||||cell3||"
        result = PlainTextBlockParser.parse(source)
        # 빈 셀은 제거되므로 cell1과 cell3만 남음
        assert result.blocks[0]["rows"][0]["cells"] == ["cell1", "cell3"]

    def test_table_with_special_characters(self):
        """특수 문자를 포함한 테이블을 파싱한다."""
        source = "||test&data||info<tag>||value\"||"
        result = PlainTextBlockParser.parse(source)
        cells = result.blocks[0]["rows"][0]["cells"]
        assert "test&data" in cells or any("test" in c for c in cells)


class TestPlainTextBlockParserTableHeaders:
    """테이블 헤더 셀 파싱 테스트."""

    def test_parses_single_header_row(self):
        """단일 헤더 행을 파싱한다."""
        source = "!!header1!!header2!!header3!!"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "table"
        assert len(result.blocks[0]["rows"]) == 1
        assert result.blocks[0]["rows"][0]["type"] == "header"
        assert result.blocks[0]["rows"][0]["cells"] == ["header1", "header2", "header3"]

    def test_parses_header_with_data_rows(self):
        """헤더와 데이터 행을 함께 파싱한다."""
        source = "!!header1!!header2!!\n||data1||data2||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        assert result.blocks[0]["type"] == "table"
        assert len(result.blocks[0]["rows"]) == 2
        assert result.blocks[0]["rows"][0]["type"] == "header"
        assert result.blocks[0]["rows"][0]["cells"] == ["header1", "header2"]
        assert result.blocks[0]["rows"][1]["type"] == "data"
        assert result.blocks[0]["rows"][1]["cells"] == ["data1", "data2"]

    def test_parses_multiple_data_rows_after_header(self):
        """헤더 행 다음에 여러 데이터 행을 파싱한다."""
        source = "!!Name!!Age!!\n||Alice||30||\n||Bob||25||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 1
        table = result.blocks[0]
        assert len(table["rows"]) == 3
        assert table["rows"][0]["type"] == "header"
        assert table["rows"][1]["type"] == "data"
        assert table["rows"][2]["type"] == "data"

    def test_header_row_followed_by_paragraph(self):
        """헤더 행 뒤의 문단을 파싱한다."""
        source = "!!col1!!col2!!\n\nFollowing paragraph."
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "table"
        assert result.blocks[1]["type"] == "paragraph"
        assert result.blocks[1]["content"] == "Following paragraph."

    def test_header_cells_trimmed(self):
        """헤더 셀의 공백을 제거한다."""
        source = "!!  header1  !!  header2  !!"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["rows"][0]["cells"] == ["header1", "header2"]

    def test_header_with_heading(self):
        """제목과 함께 있는 헤더를 파싱한다."""
        source = "= Table Title =\n\n!!Name!!Value!!"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "heading"
        assert result.blocks[1]["type"] == "table"
        assert result.blocks[1]["rows"][0]["type"] == "header"

    def test_header_row_structure_integrity(self):
        """헤더 행 구조의 무결성을 검증한다."""
        source = "!!header1!!header2!!"
        result = PlainTextBlockParser.parse(source)
        header_row = result.blocks[0]["rows"][0]
        assert "type" in header_row
        assert header_row["type"] == "header"
        assert "cells" in header_row
        assert isinstance(header_row["cells"], list)

    def test_empty_header_cell_content(self):
        """빈 헤더 셀을 처리한다."""
        source = "!!header1!!!!header3!!"
        result = PlainTextBlockParser.parse(source)
        # 빈 셀은 제거되므로 header1과 header3만 남음
        assert result.blocks[0]["rows"][0]["cells"] == ["header1", "header3"]

    def test_header_with_many_cells(self):
        """많은 셀을 가진 헤더 행을 파싱한다."""
        source = "!!a!!b!!c!!d!!e!!f!!g!!"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks[0]["rows"][0]["cells"]) == 7

    def test_header_with_special_characters(self):
        """특수 문자를 포함한 헤더를 파싱한다."""
        source = "!!test&data!!info<tag>!!value\"!!"
        result = PlainTextBlockParser.parse(source)
        cells = result.blocks[0]["rows"][0]["cells"]
        assert len(cells) > 0

    def test_mixed_header_and_data_rows(self):
        """헤더와 데이터 행이 섞여 있는 경우를 파싱한다."""
        source = "!!Col1!!Col2!!\n||Data1||Data2||\n!!SubHeader1!!SubHeader2!!\n||Data3||Data4||"
        result = PlainTextBlockParser.parse(source)
        table = result.blocks[0]
        assert len(table["rows"]) == 4
        assert table["rows"][0]["type"] == "header"
        assert table["rows"][1]["type"] == "data"
        assert table["rows"][2]["type"] == "header"
        assert table["rows"][3]["type"] == "data"

    def test_header_row_with_numeric_content(self):
        """숫자 콘텐츠를 포함한 헤더를 파싱한다."""
        source = "!!Col1!!Col2!!Col3!!\n||1||2||3||"
        result = PlainTextBlockParser.parse(source)
        assert result.blocks[0]["rows"][0]["cells"] == ["Col1", "Col2", "Col3"]
        assert result.blocks[0]["rows"][1]["cells"] == ["1", "2", "3"]

    def test_header_and_data_row_separated_by_blank_line(self):
        """빈 줄로 분리된 헤더와 데이터를 파싱한다."""
        source = "!!header1!!header2!!\n\n||data1||data2||"
        result = PlainTextBlockParser.parse(source)
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "table"
        assert result.blocks[1]["type"] == "table"
        assert result.blocks[0]["rows"][0]["type"] == "header"
        assert result.blocks[1]["rows"][0]["type"] == "data"

    def test_table_data_row_not_marked_with_type(self):
        """기존 데이터 행도 type 필드가 있는지 확인한다."""
        source = "||data1||data2||"
        result = PlainTextBlockParser.parse(source)
        row = result.blocks[0]["rows"][0]
        # 기존 동작과 호환성을 유지하기 위해 데이터 행에도 type이 있어야 함
        assert "type" in row
        assert row["type"] == "data"
