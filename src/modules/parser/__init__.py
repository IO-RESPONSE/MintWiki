"""Parser module package."""
from modules.parser.model import ParserDiagnostic, ParserResult
from modules.parser.fixtures import ParserFixtureLoader, ParserFixture
from modules.parser.parser import PlainTextBlockParser

# 파서 버전 상수
PARSER_VERSION = "1.0.0"

__all__ = ["ParserDiagnostic", "ParserResult", "ParserFixtureLoader", "ParserFixture", "PlainTextBlockParser", "PARSER_VERSION"]
