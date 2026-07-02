"""검색 결과 캐시 키 빌더."""
import hashlib
from typing import Optional


def build_search_cache_key(
    term: str,
    limit: Optional[int] = None,
    offset: int = 0,
    index_version: Optional[str] = None,
) -> str:
    """
    검색 결과 캐시를 위한 키를 생성한다.

    캐시 키는 검색어, 페이지네이션 파라미터(limit, offset), 색인 스키마 버전의
    조합으로부터 생성되는 결정적 문자열이다. `modules.cache.build_render_cache_key`와
    동일한 버전 스코프 방식을 따르므로, 색인 스키마 버전이 바뀌면 기존 캐시가
    자동으로 무효화된다.

    Args:
        term: 검색어
        limit: 반환할 최대 결과 개수 (선택사항, 기본값 None)
        offset: 건너뛸 결과 개수 (기본값 0)
        index_version: 대상 색인 스키마 버전 (선택사항, 기본값은 SEARCH_INDEX_VERSION)

    Returns:
        캐시 키 문자열 (형식: "search:v{색인 버전}:{조합 해시}")
    """
    if index_version is None:
        # 패키지 __init__ 완료 이후에만 존재하는 상수이므로 순환 import를
        # 피하기 위해 지연 import한다.
        from modules.search import SEARCH_INDEX_VERSION

        index_version = SEARCH_INDEX_VERSION

    combined = f"{term}\x00{limit}\x00{offset}"
    content_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    return f"search:v{index_version}:{content_hash}"
