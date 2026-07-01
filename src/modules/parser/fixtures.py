"""파서 테스트 픽스처 로더."""
from typing import Dict, List, Any, NamedTuple

from modules.parser.model import ParserResult


class ParserFixture(NamedTuple):
    """
    파서 테스트 픽스처.

    소스 텍스트와 예상되는 파싱 결과를 포함한다.
    """
    name: str
    source: str
    expected_result: ParserResult


class ParserFixtureLoader:
    """파서 테스트 픽스처 로더."""

    @staticmethod
    def load_all() -> List[ParserFixture]:
        """
        모든 파서 테스트 픽스처를 로드한다.

        Returns:
            파서 테스트 픽스처 목록
        """
        return [
            ParserFixtureLoader._empty_document(),
            ParserFixtureLoader._simple_paragraph(),
            ParserFixtureLoader._heading_with_text(),
            ParserFixtureLoader._multiple_blocks(),
            ParserFixtureLoader._links_and_metadata(),
            ParserFixtureLoader._complex_document(),
            ParserFixtureLoader._escaped_html_text(),
            ParserFixtureLoader._links_with_labels(),
        ]

    @staticmethod
    def load_by_name(name: str) -> ParserFixture:
        """
        이름으로 특정 파서 테스트 픽스처를 로드한다.

        Args:
            name: 픽스처 이름

        Returns:
            파서 테스트 픽스처

        Raises:
            ValueError: 해당 이름의 픽스처가 없음
        """
        fixtures = {f.name: f for f in ParserFixtureLoader.load_all()}
        if name not in fixtures:
            raise ValueError(f"Unknown fixture: {name}")
        return fixtures[name]

    @staticmethod
    def _empty_document() -> ParserFixture:
        """빈 문서 픽스처."""
        return ParserFixture(
            name="empty_document",
            source="",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _simple_paragraph() -> ParserFixture:
        """단순 문단 픽스처."""
        return ParserFixture(
            name="simple_paragraph",
            source="Hello, World!",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "Hello, World!"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _heading_with_text() -> ParserFixture:
        """제목과 텍스트 픽스처."""
        return ParserFixture(
            name="heading_with_text",
            source="= Title =\n\nContent here.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Title"},
                    {"type": "paragraph", "content": "Content here."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [
                        {"level": 1, "text": "Title"},
                    ],
                },
            ),
        )

    @staticmethod
    def _multiple_blocks() -> ParserFixture:
        """여러 블록 픽스처."""
        return ParserFixture(
            name="multiple_blocks",
            source="= Heading =\n\nFirst paragraph.\n\nSecond paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Heading"},
                    {"type": "paragraph", "content": "First paragraph."},
                    {"type": "paragraph", "content": "Second paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [
                        {"level": 1, "text": "Heading"},
                    ],
                },
            ),
        )

    @staticmethod
    def _links_and_metadata() -> ParserFixture:
        """링크와 메타데이터 픽스처."""
        return ParserFixture(
            name="links_and_metadata",
            source="[[Category:Test]]\n\nSee [[Document1]] for details.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "See [[Document1]] for details."},
                ],
                metadata={
                    "links": ["Document1"],
                    "categories": ["Test"],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _complex_document() -> ParserFixture:
        """복잡한 문서 픽스처."""
        return ParserFixture(
            name="complex_document",
            source=(
                "[[Category:Wiki]]\n"
                "[[Redirect:NewPage]]\n"
                "= Main Title =\n"
                "\n"
                "Introduction paragraph.\n"
                "\n"
                "== Section 1 ==\n"
                "\n"
                "See [[Link1]] and [[Link2]].\n"
                "\n"
                "== Section 2 ==\n"
                "\n"
                "More content."
            ),
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Main Title"},
                    {"type": "paragraph", "content": "Introduction paragraph."},
                    {"type": "heading", "level": 2, "content": "Section 1"},
                    {
                        "type": "paragraph",
                        "content": "See [[Link1]] and [[Link2]].",
                    },
                    {"type": "heading", "level": 2, "content": "Section 2"},
                    {"type": "paragraph", "content": "More content."},
                ],
                metadata={
                    "links": ["Link1", "Link2"],
                    "categories": ["Wiki"],
                    "redirects": [{"from": "Main Title", "to": "NewPage"}],
                    "headings": [
                        {"level": 1, "text": "Main Title"},
                        {"level": 2, "text": "Section 1"},
                        {"level": 2, "text": "Section 2"},
                    ],
                },
            ),
        )

    @staticmethod
    def _escaped_html_text() -> ParserFixture:
        """이스케이프된 HTML 텍스트 픽스처."""
        return ParserFixture(
            name="escaped_html_text",
            source="This has &lt;tag&gt; in it.\n\nAlso &amp; and &quot; here.",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "paragraph",
                        "content": "This has &lt;tag&gt; in it.",
                        "has_escaped_html": True,
                    },
                    {
                        "type": "paragraph",
                        "content": "Also &amp; and &quot; here.",
                        "has_escaped_html": True,
                    },
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _links_with_labels() -> ParserFixture:
        """레이블이 있는 내부 링크 픽스처."""
        return ParserFixture(
            name="links_with_labels",
            source="See [[Document1|this document]] and [[Document2|another one]] for details.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "See [[Document1|this document]] and [[Document2|another one]] for details."},
                ],
                metadata={
                    "links": ["Document1", "Document2"],
                    "categories": [],
                    "headings": [],
                },
            ),
        )
