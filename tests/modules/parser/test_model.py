"""파서 모델 테스트."""
from modules.parser.model import ParserResult


class TestParserResultConstruction:
    """파싱 결과 생성 테스트."""

    def test_creates_parser_result_with_empty_blocks(self):
        """빈 블록으로 파싱 결과를 생성한다."""
        result = ParserResult(blocks=[], metadata={})
        assert result.blocks == []
        assert result.metadata == {}

    def test_creates_parser_result_with_blocks(self):
        """블록들로 파싱 결과를 생성한다."""
        blocks = [
            {"type": "paragraph", "content": "Hello, World!"},
            {"type": "heading", "level": 1, "content": "Title"},
        ]
        result = ParserResult(blocks=blocks, metadata={})
        assert result.blocks == blocks
        assert len(result.blocks) == 2
        assert result.blocks[0]["type"] == "paragraph"
        assert result.blocks[1]["type"] == "heading"

    def test_creates_parser_result_with_metadata(self):
        """메타데이터를 포함하여 파싱 결과를 생성한다."""
        blocks = [{"type": "paragraph", "content": "Text"}]
        metadata = {
            "links": ["Document1", "Document2"],
            "categories": ["Category1"],
            "headings": [{"level": 1, "text": "Title"}],
        }
        result = ParserResult(blocks=blocks, metadata=metadata)
        assert result.blocks == blocks
        assert result.metadata == metadata
        assert result.metadata["links"] == ["Document1", "Document2"]
        assert result.metadata["categories"] == ["Category1"]

    def test_creates_parser_result_with_complex_metadata(self):
        """복잡한 메타데이터를 포함하여 파싱 결과를 생성한다."""
        blocks = [
            {"type": "paragraph", "content": "Text"},
            {"type": "link", "target": "Document1"},
        ]
        metadata = {
            "links": ["Document1", "Document2"],
            "categories": ["Category1", "Category2"],
            "redirects": [{"from": "OldName", "to": "NewName"}],
            "headings": [
                {"level": 1, "text": "Main Title"},
                {"level": 2, "text": "Section"},
            ],
            "transclusions": ["Template1", "Template2"],
        }
        result = ParserResult(blocks=blocks, metadata=metadata)
        assert result.blocks == blocks
        assert result.metadata == metadata
        assert "links" in result.metadata
        assert "redirects" in result.metadata
        assert "transclusions" in result.metadata
