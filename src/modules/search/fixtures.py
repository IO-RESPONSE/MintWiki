"""검색 모듈 테스트용 고정 문서(fixture) 로더."""
from typing import List

from modules.search.document import SearchDocument


class SearchFixtureLoader:
    """어댑터/서비스/재색인 테스트에서 재사용할 SearchDocument 픽스처를 제공한다."""

    @staticmethod
    def load_all() -> List[SearchDocument]:
        """
        모든 검색 픽스처 문서를 로드한다.

        Returns:
            검색 픽스처 문서 목록
        """
        return [
            SearchFixtureLoader._title_only_document(),
            SearchFixtureLoader._title_and_body_document(),
            SearchFixtureLoader._redirect_document(),
            SearchFixtureLoader._categorized_document(),
            SearchFixtureLoader._full_document(),
        ]

    @staticmethod
    def load_by_id(document_id: str) -> SearchDocument:
        """
        document_id로 특정 검색 픽스처 문서를 로드한다.

        Args:
            document_id: 픽스처 문서의 id

        Returns:
            검색 픽스처 문서

        Raises:
            ValueError: 해당 id의 픽스처 문서가 없음
        """
        documents = {doc.document_id: doc for doc in SearchFixtureLoader.load_all()}
        if document_id not in documents:
            raise ValueError(f"Unknown fixture document: {document_id}")
        return documents[document_id]

    @staticmethod
    def _title_only_document() -> SearchDocument:
        """본문 없이 제목만 있는 문서 픽스처."""
        return SearchDocument(document_id="fixture-title-only", title="Hello World")

    @staticmethod
    def _title_and_body_document() -> SearchDocument:
        """제목과 본문이 모두 있는 문서 픽스처."""
        return SearchDocument(
            document_id="fixture-title-and-body",
            title="Apple Pie Recipe",
            body="A simple recipe for baking a classic apple pie at home.",
        )

    @staticmethod
    def _redirect_document() -> SearchDocument:
        """다른 문서로 리다이렉트되는 문서 픽스처."""
        return SearchDocument(
            document_id="fixture-redirect",
            title="Old Title",
            redirect_target="New Title",
        )

    @staticmethod
    def _categorized_document() -> SearchDocument:
        """카테고리가 지정된 문서 픽스처."""
        return SearchDocument(
            document_id="fixture-categorized",
            title="Wiki Engine Overview",
            categories=["Documentation", "Wiki"],
        )

    @staticmethod
    def _full_document() -> SearchDocument:
        """제목/본문/카테고리를 모두 갖춘 문서 픽스처."""
        return SearchDocument(
            document_id="fixture-full",
            title="Search Adapter Design",
            body="Describes the abstract SearchAdapter interface and its implementations.",
            categories=["Documentation", "Search"],
        )


__all__ = ["SearchFixtureLoader"]
