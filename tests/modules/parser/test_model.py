"""파서 모델 테스트."""
from modules.parser.model import ParserDiagnostic, ParserResult


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


class TestParserDiagnosticConstruction:
    """파서 진단 정보 생성 테스트."""

    def test_creates_parser_diagnostic_with_error(self):
        """오류 진단을 생성한다."""
        diagnostic = ParserDiagnostic(
            message="Unexpected token",
            severity="error",
            line=1,
            column=5,
        )
        assert diagnostic.message == "Unexpected token"
        assert diagnostic.severity == "error"
        assert diagnostic.line == 1
        assert diagnostic.column == 5
        assert diagnostic.code is None

    def test_creates_parser_diagnostic_with_warning(self):
        """경고 진단을 생성한다."""
        diagnostic = ParserDiagnostic(
            message="Deprecated syntax",
            severity="warning",
            line=10,
            column=15,
        )
        assert diagnostic.message == "Deprecated syntax"
        assert diagnostic.severity == "warning"
        assert diagnostic.line == 10
        assert diagnostic.column == 15

    def test_creates_parser_diagnostic_with_info(self):
        """정보 진단을 생성한다."""
        diagnostic = ParserDiagnostic(
            message="Extra whitespace found",
            severity="info",
            line=5,
            column=8,
        )
        assert diagnostic.message == "Extra whitespace found"
        assert diagnostic.severity == "info"
        assert diagnostic.line == 5
        assert diagnostic.column == 8

    def test_creates_parser_diagnostic_with_code(self):
        """진단 코드를 포함하여 진단을 생성한다."""
        diagnostic = ParserDiagnostic(
            message="Unclosed bracket",
            severity="error",
            line=3,
            column=12,
            code="E001",
        )
        assert diagnostic.message == "Unclosed bracket"
        assert diagnostic.severity == "error"
        assert diagnostic.line == 3
        assert diagnostic.column == 12
        assert diagnostic.code == "E001"

    def test_creates_parser_diagnostic_with_different_codes(self):
        """다양한 진단 코드로 진단을 생성한다."""
        error_diagnostic = ParserDiagnostic(
            message="Syntax error",
            severity="error",
            line=1,
            column=1,
            code="E002",
        )
        warning_diagnostic = ParserDiagnostic(
            message="Syntax warning",
            severity="warning",
            line=1,
            column=1,
            code="W001",
        )
        assert error_diagnostic.code == "E002"
        assert warning_diagnostic.code == "W001"
