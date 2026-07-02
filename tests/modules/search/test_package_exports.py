"""search 패키지 export 테스트."""
import modules.search as search


class TestSearchPackageExports:
    """search 패키지가 정상적으로 import 가능한지 검증한다."""

    def test_package_is_importable(self):
        """search 패키지를 import할 수 있다."""
        assert search is not None

    def test_all_matches_declared_exports(self):
        """__all__ 에 선언된 이름이 실제 모듈 속성으로 존재한다.

        본문 검색/리다이렉트 검색 등 추가 인덱싱 계약은 후속 태스크에서
        추가되므로, 현재는 검색 문서 모델(SearchDocument), 검색 질의
        모델(SearchQuery, 페이지네이션 파라미터 포함), 검색 결과 모델
        (SearchResult), 검색 어댑터 인터페이스(SearchAdapter), 메모리
        기반 검색 어댑터 구현(InMemorySearchAdapter), Meilisearch 검색
        어댑터 골격(MeilisearchSearchAdapter), OpenSearch 검색 어댑터
        골격(OpenSearchSearchAdapter), 어댑터로 위임하는 검색 서비스
        골격(SearchService), 문서 색인 작업 페이로드
        (IndexDocumentJobPayload), 사용할 검색 어댑터 구현을 고르는 설정
        (SearchAdapterConfig), 한국어 텍스트 정규화 자리표시자
        (normalize_korean_text), 그리고 그 오류 타입들만 export한다.
        """
        assert search.__all__ == [
            "SearchDocument",
            "EmptySearchDocumentIdError",
            "EmptySearchDocumentTitleError",
            "SearchQuery",
            "EmptySearchQueryTermError",
            "InvalidSearchQueryLimitError",
            "InvalidSearchQueryOffsetError",
            "SearchResult",
            "InvalidSearchResultScoreError",
            "SearchAdapter",
            "InMemorySearchAdapter",
            "MeilisearchSearchAdapter",
            "OpenSearchSearchAdapter",
            "SearchService",
            "IndexDocumentJobPayload",
            "SearchAdapterConfig",
            "InvalidSearchAdapterBackendError",
            "normalize_korean_text",
        ]
        for name in search.__all__:
            assert hasattr(search, name)
