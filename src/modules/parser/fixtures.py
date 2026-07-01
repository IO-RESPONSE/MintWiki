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
            ParserFixtureLoader._external_link_simple(),
            ParserFixtureLoader._external_links_multiple(),
            ParserFixtureLoader._external_link_with_label(),
            ParserFixtureLoader._bold_simple(),
            ParserFixtureLoader._bold_multiple(),
            ParserFixtureLoader._bold_with_special_chars(),
            ParserFixtureLoader._italic_simple(),
            ParserFixtureLoader._italic_multiple(),
            ParserFixtureLoader._italic_with_special_chars(),
            ParserFixtureLoader._strike_simple(),
            ParserFixtureLoader._strike_multiple(),
            ParserFixtureLoader._strike_with_special_chars(),
            ParserFixtureLoader._bold_with_nested_italic(),
            ParserFixtureLoader._italic_with_nested_bold(),
            ParserFixtureLoader._bold_with_nested_strike(),
            ParserFixtureLoader._italic_with_nested_strike(),
            ParserFixtureLoader._unordered_list_simple(),
            ParserFixtureLoader._unordered_list_multiple(),
            ParserFixtureLoader._unordered_list_nested(),
            ParserFixtureLoader._unordered_list_with_special_chars(),
            ParserFixtureLoader._ordered_list_simple(),
            ParserFixtureLoader._ordered_list_multiple(),
            ParserFixtureLoader._ordered_list_nested(),
            ParserFixtureLoader._ordered_list_with_special_chars(),
            ParserFixtureLoader._horizontal_rule_simple(),
            ParserFixtureLoader._horizontal_rule_with_text(),
            ParserFixtureLoader._horizontal_rule_multiple(),
            ParserFixtureLoader._line_break_simple(),
            ParserFixtureLoader._line_break_with_text(),
            ParserFixtureLoader._line_break_multiple(),
            ParserFixtureLoader._nowiki_simple(),
            ParserFixtureLoader._nowiki_with_wiki_markup(),
            ParserFixtureLoader._nowiki_multiline(),
            ParserFixtureLoader._nowiki_with_text(),
            ParserFixtureLoader._nowiki_with_special_chars(),
            ParserFixtureLoader._nowiki_multiple(),
            ParserFixtureLoader._code_simple(),
            ParserFixtureLoader._code_with_syntax(),
            ParserFixtureLoader._code_multiline(),
            ParserFixtureLoader._code_with_text(),
            ParserFixtureLoader._code_with_special_chars(),
            ParserFixtureLoader._code_multiple(),
            ParserFixtureLoader._redirect_simple(),
            ParserFixtureLoader._redirect_with_heading(),
            ParserFixtureLoader._redirect_with_category(),
            ParserFixtureLoader._redirect_with_content(),
            ParserFixtureLoader._categories_simple(),
            ParserFixtureLoader._categories_multiple(),
            ParserFixtureLoader._categories_with_heading(),
            ParserFixtureLoader._categories_with_content(),
            ParserFixtureLoader._categories_with_special_chars(),
            ParserFixtureLoader._backlinks_simple(),
            ParserFixtureLoader._backlinks_multiple(),
            ParserFixtureLoader._backlinks_with_heading(),
            ParserFixtureLoader._backlinks_with_content(),
            ParserFixtureLoader._backlinks_with_special_chars(),
            ParserFixtureLoader._table_simple(),
            ParserFixtureLoader._table_multiple_rows(),
            ParserFixtureLoader._table_with_heading(),
            ParserFixtureLoader._table_with_content(),
            ParserFixtureLoader._table_header_simple(),
            ParserFixtureLoader._table_header_with_data(),
            ParserFixtureLoader._table_header_with_heading(),
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

    @staticmethod
    def _external_link_simple() -> ParserFixture:
        """단순 외부 링크 픽스처."""
        return ParserFixture(
            name="external_link_simple",
            source="Visit [https://example.com] for more info.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "Visit [https://example.com] for more info."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "external_links": ["https://example.com"],
                },
            ),
        )

    @staticmethod
    def _external_links_multiple() -> ParserFixture:
        """여러 외부 링크 픽스처."""
        return ParserFixture(
            name="external_links_multiple",
            source="Check [https://site1.com] and [https://site2.com] now.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "Check [https://site1.com] and [https://site2.com] now."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "external_links": ["https://site1.com", "https://site2.com"],
                },
            ),
        )

    @staticmethod
    def _external_link_with_label() -> ParserFixture:
        """레이블이 있는 외부 링크 픽스처."""
        return ParserFixture(
            name="external_link_with_label",
            source="Visit [https://example.com our site] for details.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "Visit [https://example.com our site] for details."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "external_links": ["https://example.com"],
                },
            ),
        )

    @staticmethod
    def _bold_simple() -> ParserFixture:
        """단순 굵은 텍스트 픽스처."""
        return ParserFixture(
            name="bold_simple",
            source="This is '''bold text''' in a paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is '''bold text''' in a paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _bold_multiple() -> ParserFixture:
        """여러 개의 굵은 텍스트 픽스처."""
        return ParserFixture(
            name="bold_multiple",
            source="This has '''first bold''' and '''second bold''' text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This has '''first bold''' and '''second bold''' text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _bold_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 굵은 텍스트 픽스처."""
        return ParserFixture(
            name="bold_with_special_chars",
            source="This is '''bold & important!''' text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is '''bold & important!''' text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _italic_simple() -> ParserFixture:
        """단순 이탤릭 텍스트 픽스처."""
        return ParserFixture(
            name="italic_simple",
            source="This is ''italic text'' in a paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ''italic text'' in a paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _italic_multiple() -> ParserFixture:
        """여러 개의 이탤릭 텍스트 픽스처."""
        return ParserFixture(
            name="italic_multiple",
            source="This has ''first italic'' and ''second italic'' text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This has ''first italic'' and ''second italic'' text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _italic_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 이탤릭 텍스트 픽스처."""
        return ParserFixture(
            name="italic_with_special_chars",
            source="This is ''italic & emphasized!'' text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ''italic & emphasized!'' text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _strike_simple() -> ParserFixture:
        """단순 취소선 텍스트 픽스처."""
        return ParserFixture(
            name="strike_simple",
            source="This is ~~strikethrough text~~ in a paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ~~strikethrough text~~ in a paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _strike_multiple() -> ParserFixture:
        """여러 개의 취소선 텍스트 픽스처."""
        return ParserFixture(
            name="strike_multiple",
            source="This has ~~first strike~~ and ~~second strike~~ text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This has ~~first strike~~ and ~~second strike~~ text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _strike_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 취소선 텍스트 픽스처."""
        return ParserFixture(
            name="strike_with_special_chars",
            source="This is ~~strike & obsolete!~~ text.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ~~strike & obsolete!~~ text."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _bold_with_nested_italic() -> ParserFixture:
        """이탤릭이 중첩된 굵은 텍스트 픽스처."""
        return ParserFixture(
            name="bold_with_nested_italic",
            source="This is '''bold ''italic'' text''' here.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is '''bold ''italic'' text''' here."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _italic_with_nested_bold() -> ParserFixture:
        """굵은 텍스트가 중첩된 이탤릭 픽스처."""
        return ParserFixture(
            name="italic_with_nested_bold",
            source="This is ''italic '''bold''' text'' here.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ''italic '''bold''' text'' here."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _bold_with_nested_strike() -> ParserFixture:
        """취소선이 중첩된 굵은 텍스트 픽스처."""
        return ParserFixture(
            name="bold_with_nested_strike",
            source="This is '''bold ~~strikethrough~~ text''' here.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is '''bold ~~strikethrough~~ text''' here."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _italic_with_nested_strike() -> ParserFixture:
        """취소선이 중첩된 이탤릭 픽스처."""
        return ParserFixture(
            name="italic_with_nested_strike",
            source="This is ''italic ~~strikethrough~~ text'' here.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is ''italic ~~strikethrough~~ text'' here."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _unordered_list_simple() -> ParserFixture:
        """단순 순서 없는 목록 픽스처."""
        return ParserFixture(
            name="unordered_list_simple",
            source="* Item 1\n* Item 2",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "unordered",
                        "items": [
                            {"level": 1, "text": "Item 1", "children": []},
                            {"level": 1, "text": "Item 2", "children": []},
                        ],
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
    def _unordered_list_multiple() -> ParserFixture:
        """여러 개의 항목을 가진 순서 없는 목록 픽스처."""
        return ParserFixture(
            name="unordered_list_multiple",
            source="* First item\n* Second item\n* Third item",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "unordered",
                        "items": [
                            {"level": 1, "text": "First item", "children": []},
                            {"level": 1, "text": "Second item", "children": []},
                            {"level": 1, "text": "Third item", "children": []},
                        ],
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
    def _unordered_list_nested() -> ParserFixture:
        """중첩된 순서 없는 목록 픽스처."""
        return ParserFixture(
            name="unordered_list_nested",
            source="* Item 1\n** Nested 1.1\n** Nested 1.2\n* Item 2",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "unordered",
                        "items": [
                            {
                                "level": 1,
                                "text": "Item 1",
                                "children": [
                                    {"level": 2, "text": "Nested 1.1", "children": []},
                                    {"level": 2, "text": "Nested 1.2", "children": []},
                                ],
                            },
                            {"level": 1, "text": "Item 2", "children": []},
                        ],
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
    def _unordered_list_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 순서 없는 목록 픽스처."""
        return ParserFixture(
            name="unordered_list_with_special_chars",
            source="* Item with & special!\n* Item with 123 numbers",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "unordered",
                        "items": [
                            {"level": 1, "text": "Item with & special!", "children": []},
                            {"level": 1, "text": "Item with 123 numbers", "children": []},
                        ],
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
    def _ordered_list_simple() -> ParserFixture:
        """단순 순서 있는 목록 픽스처."""
        return ParserFixture(
            name="ordered_list_simple",
            source="# Item 1\n# Item 2",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "ordered",
                        "items": [
                            {"level": 1, "text": "Item 1", "children": []},
                            {"level": 1, "text": "Item 2", "children": []},
                        ],
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
    def _ordered_list_multiple() -> ParserFixture:
        """여러 개의 항목을 가진 순서 있는 목록 픽스처."""
        return ParserFixture(
            name="ordered_list_multiple",
            source="# First item\n# Second item\n# Third item",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "ordered",
                        "items": [
                            {"level": 1, "text": "First item", "children": []},
                            {"level": 1, "text": "Second item", "children": []},
                            {"level": 1, "text": "Third item", "children": []},
                        ],
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
    def _ordered_list_nested() -> ParserFixture:
        """중첩된 순서 있는 목록 픽스처."""
        return ParserFixture(
            name="ordered_list_nested",
            source="# Item 1\n## Nested 1.1\n## Nested 1.2\n# Item 2",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "ordered",
                        "items": [
                            {
                                "level": 1,
                                "text": "Item 1",
                                "children": [
                                    {"level": 2, "text": "Nested 1.1", "children": []},
                                    {"level": 2, "text": "Nested 1.2", "children": []},
                                ],
                            },
                            {"level": 1, "text": "Item 2", "children": []},
                        ],
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
    def _ordered_list_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 순서 있는 목록 픽스처."""
        return ParserFixture(
            name="ordered_list_with_special_chars",
            source="# Item with & special!\n# Item with 123 numbers",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "list",
                        "list_type": "ordered",
                        "items": [
                            {"level": 1, "text": "Item with & special!", "children": []},
                            {"level": 1, "text": "Item with 123 numbers", "children": []},
                        ],
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
    def _horizontal_rule_simple() -> ParserFixture:
        """간단한 수평선 픽스처."""
        return ParserFixture(
            name="horizontal_rule_simple",
            source="----",
            expected_result=ParserResult(
                blocks=[
                    {"type": "horizontal_rule"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _horizontal_rule_with_text() -> ParserFixture:
        """텍스트와 함께 있는 수평선 픽스처."""
        return ParserFixture(
            name="horizontal_rule_with_text",
            source="= Title =\n\nContent here.\n\n----\n\nMore content.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Title"},
                    {"type": "paragraph", "content": "Content here."},
                    {"type": "horizontal_rule"},
                    {"type": "paragraph", "content": "More content."},
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
    def _horizontal_rule_multiple() -> ParserFixture:
        """여러 개의 수평선 픽스처."""
        return ParserFixture(
            name="horizontal_rule_multiple",
            source="----\n\n----\n\n-----",
            expected_result=ParserResult(
                blocks=[
                    {"type": "horizontal_rule"},
                    {"type": "horizontal_rule"},
                    {"type": "horizontal_rule"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _line_break_simple() -> ParserFixture:
        """간단한 줄 바꿈 픽스처."""
        return ParserFixture(
            name="line_break_simple",
            source="\\\\",
            expected_result=ParserResult(
                blocks=[
                    {"type": "line_break"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _line_break_with_text() -> ParserFixture:
        """텍스트와 함께 있는 줄 바꿈 픽스처."""
        return ParserFixture(
            name="line_break_with_text",
            source="First line.\n\n\\\\\n\nSecond line.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "First line."},
                    {"type": "line_break"},
                    {"type": "paragraph", "content": "Second line."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _line_break_multiple() -> ParserFixture:
        """여러 개의 줄 바꿈 픽스처."""
        return ParserFixture(
            name="line_break_multiple",
            source="\\\\\n\n\\\\\n\n\\\\",
            expected_result=ParserResult(
                blocks=[
                    {"type": "line_break"},
                    {"type": "line_break"},
                    {"type": "line_break"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_simple() -> ParserFixture:
        """단순 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_simple",
            source="<nowiki>'''bold'''</nowiki>",
            expected_result=ParserResult(
                blocks=[
                    {"type": "nowiki", "content": "'''bold'''"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_with_wiki_markup() -> ParserFixture:
        """위키 마크업을 포함한 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_with_wiki_markup",
            source="<nowiki>[[Link]] and '''bold''' and ''italic''</nowiki>",
            expected_result=ParserResult(
                blocks=[
                    {"type": "nowiki", "content": "[[Link]] and '''bold''' and ''italic''"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_multiline() -> ParserFixture:
        """여러 줄의 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_multiline",
            source="<nowiki>\nFirst line\nSecond line\n</nowiki>",
            expected_result=ParserResult(
                blocks=[
                    {"type": "nowiki", "content": "First line\nSecond line"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_with_text() -> ParserFixture:
        """텍스트와 함께 있는 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_with_text",
            source="This is a paragraph.\n\n<nowiki>'''bold'''</nowiki>\n\nAnother paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is a paragraph."},
                    {"type": "nowiki", "content": "'''bold'''"},
                    {"type": "paragraph", "content": "Another paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_with_special_chars",
            source="<nowiki>< > & ' \" [[ ]] {{ }}</nowiki>",
            expected_result=ParserResult(
                blocks=[
                    {"type": "nowiki", "content": "< > & ' \" [[ ]] {{ }}"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _nowiki_multiple() -> ParserFixture:
        """여러 개의 nowiki 블록 픽스처."""
        return ParserFixture(
            name="nowiki_multiple",
            source="<nowiki>First block</nowiki>\n\n<nowiki>Second block</nowiki>",
            expected_result=ParserResult(
                blocks=[
                    {"type": "nowiki", "content": "First block"},
                    {"type": "nowiki", "content": "Second block"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_simple() -> ParserFixture:
        """단순 코드 블록 픽스처."""
        return ParserFixture(
            name="code_simple",
            source="{{{print('hello')}}}",
            expected_result=ParserResult(
                blocks=[
                    {"type": "code", "content": "print('hello')"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_with_syntax() -> ParserFixture:
        """문법을 포함한 코드 블록 픽스처."""
        return ParserFixture(
            name="code_with_syntax",
            source="{{{def foo():\n    return 42}}}",
            expected_result=ParserResult(
                blocks=[
                    {"type": "code", "content": "def foo():\n    return 42"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_multiline() -> ParserFixture:
        """여러 줄의 코드 블록 픽스처."""
        return ParserFixture(
            name="code_multiline",
            source="{{{\nFirst line\nSecond line\n}}}",
            expected_result=ParserResult(
                blocks=[
                    {"type": "code", "content": "First line\nSecond line"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_with_text() -> ParserFixture:
        """텍스트와 함께 있는 코드 블록 픽스처."""
        return ParserFixture(
            name="code_with_text",
            source="This is a paragraph.\n\n{{{x = 10}}}\n\nAnother paragraph.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This is a paragraph."},
                    {"type": "code", "content": "x = 10"},
                    {"type": "paragraph", "content": "Another paragraph."},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 코드 블록 픽스처."""
        return ParserFixture(
            name="code_with_special_chars",
            source="{{{& < > ' \" [ ] {{ # ! ~}}}",
            expected_result=ParserResult(
                blocks=[
                    {"type": "code", "content": "& < > ' \" [ ] {{ # ! ~"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _code_multiple() -> ParserFixture:
        """여러 개의 코드 블록 픽스처."""
        return ParserFixture(
            name="code_multiple",
            source="{{{First block}}}\n\n{{{Second block}}}",
            expected_result=ParserResult(
                blocks=[
                    {"type": "code", "content": "First block"},
                    {"type": "code", "content": "Second block"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _redirect_simple() -> ParserFixture:
        """단순 리다이렉트 픽스처."""
        return ParserFixture(
            name="redirect_simple",
            source="[[Redirect:NewPage]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "redirects": [{"from": "", "to": "NewPage"}],
                },
            ),
        )

    @staticmethod
    def _redirect_with_heading() -> ParserFixture:
        """제목이 있는 리다이렉트 픽스처."""
        return ParserFixture(
            name="redirect_with_heading",
            source="= Main Title =\n\n[[Redirect:TargetPage]]",
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Main Title"},
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [{"level": 1, "text": "Main Title"}],
                    "redirects": [{"from": "Main Title", "to": "TargetPage"}],
                },
            ),
        )

    @staticmethod
    def _redirect_with_category() -> ParserFixture:
        """카테고리와 리다이렉트 픽스처."""
        return ParserFixture(
            name="redirect_with_category",
            source="[[Category:Wiki]]\n[[Redirect:NewPage]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": ["Wiki"],
                    "headings": [],
                    "redirects": [{"from": "", "to": "NewPage"}],
                },
            ),
        )

    @staticmethod
    def _redirect_with_content() -> ParserFixture:
        """콘텐츠와 리다이렉트 픽스처."""
        return ParserFixture(
            name="redirect_with_content",
            source=(
                "= Old Title =\n"
                "\n"
                "[[Redirect:New Title]]\n"
                "\n"
                "Some content here.\n"
                "\n"
                "See [[Link1]] for more."
            ),
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Old Title"},
                    {"type": "paragraph", "content": "Some content here."},
                    {"type": "paragraph", "content": "See [[Link1]] for more."},
                ],
                metadata={
                    "links": ["Link1"],
                    "categories": [],
                    "headings": [{"level": 1, "text": "Old Title"}],
                    "redirects": [{"from": "Old Title", "to": "New Title"}],
                },
            ),
        )

    @staticmethod
    def _categories_simple() -> ParserFixture:
        """단순 카테고리 픽스처."""
        return ParserFixture(
            name="categories_simple",
            source="[[Category:Test]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": ["Test"],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _categories_multiple() -> ParserFixture:
        """여러 카테고리 픽스처."""
        return ParserFixture(
            name="categories_multiple",
            source="[[Category:Wiki]]\n[[Category:Technology]]\n[[Category:Science]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": ["Wiki", "Technology", "Science"],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _categories_with_heading() -> ParserFixture:
        """제목과 함께 있는 카테고리 픽스처."""
        return ParserFixture(
            name="categories_with_heading",
            source="[[Category:Documentation]]\n\n= Main Article =\n\nThis is the content.",
            expected_result=ParserResult(
                blocks=[
                    {"type": "heading", "level": 1, "content": "Main Article"},
                    {"type": "paragraph", "content": "This is the content."},
                ],
                metadata={
                    "links": [],
                    "categories": ["Documentation"],
                    "headings": [{"level": 1, "text": "Main Article"}],
                },
            ),
        )

    @staticmethod
    def _categories_with_content() -> ParserFixture:
        """콘텐츠와 함께 있는 카테고리 픽스처."""
        return ParserFixture(
            name="categories_with_content",
            source="[[Category:Tutorial]]\n\nThis paragraph contains text with [[Link1]].",
            expected_result=ParserResult(
                blocks=[
                    {"type": "paragraph", "content": "This paragraph contains text with [[Link1]]."},
                ],
                metadata={
                    "links": ["Link1"],
                    "categories": ["Tutorial"],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _categories_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 카테고리 픽스처."""
        return ParserFixture(
            name="categories_with_special_chars",
            source="[[Category:Science & Technology]]\n[[Category:2024 Events]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": ["Science & Technology", "2024 Events"],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _backlinks_simple() -> ParserFixture:
        """단순 백링크 픽스처."""
        return ParserFixture(
            name="backlinks_simple",
            source="[[Backlink:Test]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "backlinks": ["Test"],
                },
            ),
        )

    @staticmethod
    def _backlinks_multiple() -> ParserFixture:
        """여러 백링크 픽스처."""
        return ParserFixture(
            name="backlinks_multiple",
            source="[[Backlink:Page1]]\n[[Backlink:Page2]]\n[[Backlink:Page3]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "backlinks": ["Page1", "Page2", "Page3"],
                },
            ),
        )

    @staticmethod
    def _backlinks_with_heading() -> ParserFixture:
        """제목과 함께 있는 백링크 픽스처."""
        return ParserFixture(
            name="backlinks_with_heading",
            source="[[Backlink:Reference]]\n\n= Main Article =",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "heading",
                        "level": 1,
                        "content": "Main Article",
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [
                        {"level": 1, "text": "Main Article"}
                    ],
                    "backlinks": ["Reference"],
                },
            ),
        )

    @staticmethod
    def _backlinks_with_content() -> ParserFixture:
        """콘텐츠와 함께 있는 백링크 픽스처."""
        return ParserFixture(
            name="backlinks_with_content",
            source="[[Backlink:Tutorial]]\n\nSome content here.",
            expected_result=ParserResult(
                blocks=[
                    {
                        "type": "paragraph",
                        "content": "Some content here.",
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "backlinks": ["Tutorial"],
                },
            ),
        )

    @staticmethod
    def _backlinks_with_special_chars() -> ParserFixture:
        """특수 문자를 포함한 백링크 픽스처."""
        return ParserFixture(
            name="backlinks_with_special_chars",
            source="[[Backlink:Science & Technology]]\n[[Backlink:2024 Events]]",
            expected_result=ParserResult(
                blocks=[],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                    "backlinks": ["Science & Technology", "2024 Events"],
                },
            ),
        )

    @staticmethod
    def _table_simple() -> ParserFixture:
        """간단한 테이블 행 픽스처."""
        return ParserFixture(
            name="table_simple",
            source="||cell1||cell2||cell3||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'data', 'cells': ['cell1', 'cell2', 'cell3']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _table_multiple_rows() -> ParserFixture:
        """여러 행의 테이블 픽스처."""
        return ParserFixture(
            name="table_multiple_rows",
            source="||cell1||cell2||\n||cell3||cell4||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'data', 'cells': ['cell1', 'cell2']},
                            {'type': 'data', 'cells': ['cell3', 'cell4']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _table_with_heading() -> ParserFixture:
        """제목과 함께 있는 테이블 픽스처."""
        return ParserFixture(
            name="table_with_heading",
            source="= Table Title =\n||row1cell1||row1cell2||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'heading',
                        'level': 1,
                        'content': 'Table Title',
                    },
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'data', 'cells': ['row1cell1', 'row1cell2']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [
                        {'level': 1, 'text': 'Table Title'},
                    ],
                },
            ),
        )

    @staticmethod
    def _table_with_content() -> ParserFixture:
        """문단 텍스트와 함께 있는 테이블 픽스처."""
        return ParserFixture(
            name="table_with_content",
            source="This is a table:\n\n||data1||data2||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'paragraph',
                        'content': 'This is a table:',
                    },
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'data', 'cells': ['data1', 'data2']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _table_header_simple() -> ParserFixture:
        """간단한 테이블 헤더 픽스처."""
        return ParserFixture(
            name="table_header_simple",
            source="!!header1!!header2!!header3!!",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'header', 'cells': ['header1', 'header2', 'header3']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _table_header_with_data() -> ParserFixture:
        """헤더와 데이터 행을 가진 테이블 픽스처."""
        return ParserFixture(
            name="table_header_with_data",
            source="!!header1!!header2!!\n||data1||data2||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'header', 'cells': ['header1', 'header2']},
                            {'type': 'data', 'cells': ['data1', 'data2']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [],
                },
            ),
        )

    @staticmethod
    def _table_header_with_heading() -> ParserFixture:
        """제목과 함께 있는 테이블 헤더 픽스처."""
        return ParserFixture(
            name="table_header_with_heading",
            source="= Table Title =\n\n!!col1!!col2!!\n||val1||val2||",
            expected_result=ParserResult(
                blocks=[
                    {
                        'type': 'heading',
                        'level': 1,
                        'content': 'Table Title',
                    },
                    {
                        'type': 'table',
                        'rows': [
                            {'type': 'header', 'cells': ['col1', 'col2']},
                            {'type': 'data', 'cells': ['val1', 'val2']},
                        ],
                    }
                ],
                metadata={
                    "links": [],
                    "categories": [],
                    "headings": [
                        {'level': 1, 'text': 'Table Title'},
                    ],
                },
            ),
        )
