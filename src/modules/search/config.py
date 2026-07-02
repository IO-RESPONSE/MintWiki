"""검색 어댑터 설정."""
import os
from typing import Optional

ALLOWED_SEARCH_ADAPTER_BACKENDS = {"in_memory"}


class InvalidSearchAdapterBackendError(Exception):
    """지원하지 않는 검색 어댑터 backend 값이 주어졌을 때 발생."""

    pass


class SearchAdapterConfig:
    """
    사용할 검색 어댑터 구현을 선택하는 설정.

    router.py/repository.py/schema.py가 아니므로 도메인 이식성 경계 규칙에
    따라 pydantic 등 프레임워크에 의존하지 않는 순수 Python 클래스로 둔다.
    backend 값에 따라 SearchService에 주입할 SearchAdapter 구현체를 고르는
    데 쓰인다. 현재는 로컬 폴백 어댑터(InMemorySearchAdapter)만 구현되어
    있으며, meilisearch/opensearch 등 외부 검색 엔진 어댑터는 이후 태스크에서
    추가된다.
    """

    def __init__(self, backend: Optional[str] = None):
        """
        검색 어댑터 설정을 생성한다.

        Args:
            backend: 사용할 어댑터 종류. 생략하면 WIKI_SEARCH_BACKEND
                환경 변수를 사용하고, 그것도 없으면 "in_memory"를 사용한다.

        Raises:
            InvalidSearchAdapterBackendError: backend가 지원하지 않는 값인 경우
        """
        resolved = backend if backend is not None else os.environ.get("WIKI_SEARCH_BACKEND", "in_memory")
        if resolved not in ALLOWED_SEARCH_ADAPTER_BACKENDS:
            raise InvalidSearchAdapterBackendError(f"지원하지 않는 backend 입니다: {resolved!r}")

        self.backend = resolved
