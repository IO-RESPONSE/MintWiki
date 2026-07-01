"""파서 픽스처 로더 테스트."""
import pytest
from modules.parser import ParserFixtureLoader, ParserFixture
from modules.parser.model import ParserResult


class TestParserFixtureLoaderLoadAll:
    """픽스처 로더의 load_all 메서드 테스트."""

    def test_loads_all_fixtures(self):
        """모든 파서 픽스처를 로드한다."""
        fixtures = ParserFixtureLoader.load_all()
        assert len(fixtures) > 0

    def test_returns_list_of_parser_fixtures(self):
        """ParserFixture 타입의 리스트를 반환한다."""
        fixtures = ParserFixtureLoader.load_all()
        assert all(isinstance(f, ParserFixture) for f in fixtures)

    def test_each_fixture_has_required_fields(self):
        """각 픽스처는 필수 필드를 가진다."""
        fixtures = ParserFixtureLoader.load_all()
        for fixture in fixtures:
            assert fixture.name
            assert isinstance(fixture.source, str)
            assert isinstance(fixture.expected_result, ParserResult)

    def test_fixture_names_are_unique(self):
        """픽스처 이름이 고유하다."""
        fixtures = ParserFixtureLoader.load_all()
        names = [f.name for f in fixtures]
        assert len(names) == len(set(names))

    def test_all_fixtures_have_valid_results(self):
        """모든 픽스처의 결과가 유효하다."""
        fixtures = ParserFixtureLoader.load_all()
        for fixture in fixtures:
            assert isinstance(fixture.expected_result.blocks, list)
            assert isinstance(fixture.expected_result.metadata, dict)


class TestParserFixtureLoaderLoadByName:
    """픽스처 로더의 load_by_name 메서드 테스트."""

    def test_loads_empty_document_fixture(self):
        """빈 문서 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("empty_document")
        assert fixture.name == "empty_document"
        assert fixture.source == ""
        assert fixture.expected_result.blocks == []

    def test_loads_simple_paragraph_fixture(self):
        """단순 문단 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("simple_paragraph")
        assert fixture.name == "simple_paragraph"
        assert fixture.source == "Hello, World!"
        assert len(fixture.expected_result.blocks) == 1

    def test_loads_heading_with_text_fixture(self):
        """제목과 텍스트 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("heading_with_text")
        assert fixture.name == "heading_with_text"
        assert "= Title =" in fixture.source
        assert len(fixture.expected_result.blocks) == 2

    def test_loads_multiple_blocks_fixture(self):
        """여러 블록 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("multiple_blocks")
        assert fixture.name == "multiple_blocks"
        assert len(fixture.expected_result.blocks) == 3

    def test_loads_links_and_metadata_fixture(self):
        """링크와 메타데이터 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("links_and_metadata")
        assert fixture.name == "links_and_metadata"
        assert "Category:Test" in fixture.source
        assert "Document1" in fixture.expected_result.metadata["links"]

    def test_loads_complex_document_fixture(self):
        """복잡한 문서 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("complex_document")
        assert fixture.name == "complex_document"
        assert fixture.expected_result.metadata["categories"] == ["Wiki"]
        assert len(fixture.expected_result.metadata["headings"]) == 3

    def test_raises_error_for_unknown_fixture(self):
        """존재하지 않는 픽스처 이름으로 오류를 발생시킨다."""
        with pytest.raises(ValueError, match="Unknown fixture"):
            ParserFixtureLoader.load_by_name("nonexistent_fixture")

    def test_raises_error_with_meaningful_message(self):
        """의미 있는 오류 메시지를 포함한다."""
        try:
            ParserFixtureLoader.load_by_name("bad_fixture_name")
        except ValueError as e:
            assert "bad_fixture_name" in str(e)


class TestParserFixtureContent:
    """파서 픽스처의 내용 테스트."""

    def test_empty_document_has_empty_blocks(self):
        """빈 문서는 빈 블록을 가진다."""
        fixture = ParserFixtureLoader.load_by_name("empty_document")
        assert fixture.expected_result.blocks == []
        assert fixture.expected_result.metadata["links"] == []
        assert fixture.expected_result.metadata["categories"] == []

    def test_heading_fixture_has_correct_level(self):
        """제목 픽스처가 올바른 레벨을 가진다."""
        fixture = ParserFixtureLoader.load_by_name("heading_with_text")
        heading_block = fixture.expected_result.blocks[0]
        assert heading_block["type"] == "heading"
        assert heading_block["level"] == 1

    def test_complex_document_has_all_metadata(self):
        """복잡한 문서는 모든 메타데이터를 가진다."""
        fixture = ParserFixtureLoader.load_by_name("complex_document")
        metadata = fixture.expected_result.metadata
        assert "links" in metadata
        assert "categories" in metadata
        assert "headings" in metadata
        assert len(metadata["links"]) == 2
        assert metadata["links"] == ["Link1", "Link2"]

    def test_loads_categories_simple_fixture(self):
        """단순 카테고리 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("categories_simple")
        assert fixture.name == "categories_simple"
        assert fixture.source == "[[Category:Test]]"
        assert fixture.expected_result.metadata["categories"] == ["Test"]

    def test_loads_categories_multiple_fixture(self):
        """여러 카테고리 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("categories_multiple")
        assert fixture.name == "categories_multiple"
        assert fixture.expected_result.metadata["categories"] == [
            "Wiki",
            "Technology",
            "Science",
        ]

    def test_loads_categories_with_heading_fixture(self):
        """제목과 함께 있는 카테고리 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("categories_with_heading")
        assert fixture.name == "categories_with_heading"
        assert fixture.expected_result.metadata["categories"] == ["Documentation"]
        assert len(fixture.expected_result.blocks) == 2

    def test_loads_categories_with_content_fixture(self):
        """콘텐츠와 함께 있는 카테고리 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("categories_with_content")
        assert fixture.name == "categories_with_content"
        assert fixture.expected_result.metadata["categories"] == ["Tutorial"]
        assert fixture.expected_result.metadata["links"] == ["Link1"]

    def test_loads_categories_with_special_chars_fixture(self):
        """특수 문자를 포함한 카테고리 픽스처를 로드한다."""
        fixture = ParserFixtureLoader.load_by_name("categories_with_special_chars")
        assert fixture.name == "categories_with_special_chars"
        assert fixture.expected_result.metadata["categories"] == [
            "Science & Technology",
            "2024 Events",
        ]
