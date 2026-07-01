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
