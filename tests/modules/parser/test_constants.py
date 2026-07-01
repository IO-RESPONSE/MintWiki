"""파서 모듈 상수 테스트."""
import modules.parser as parser_module


class TestParserVersionConstant:
    """파서 버전 상수 테스트."""

    def test_parser_version_is_defined(self):
        """파서 버전 상수가 정의되어 있다."""
        assert hasattr(parser_module, "PARSER_VERSION")

    def test_parser_version_is_string(self):
        """파서 버전 상수는 문자열 타입이다."""
        assert isinstance(parser_module.PARSER_VERSION, str)

    def test_parser_version_format(self):
        """파서 버전 상수는 semantic versioning 형식이다."""
        version = parser_module.PARSER_VERSION
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_parser_version_is_accessible_from_init(self):
        """파서 모듈의 __init__.py에서 버전 상수가 export되어 있다."""
        from modules.parser import PARSER_VERSION
        assert PARSER_VERSION == "1.0.0"
