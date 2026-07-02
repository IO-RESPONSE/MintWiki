"""렌더 캐시 키 빌더."""
import hashlib


def build_render_cache_key(source: str, parser_version: str) -> str:
    """
    렌더링 결과 캐시를 위한 키를 생성한다.

    캐시 키는 소스 문본과 파서 버전의 조합으로부터 생성되는 결정적 문자열이다.
    파서 버전이 변경되면 기존 캐시가 자동으로 무효화된다.

    Args:
        source: 렌더링할 위키마크업 소스 문본
        parser_version: 사용 중인 파서의 버전 (예: "1.0.0")

    Returns:
        캐시 키 문자열 (형식: "render:v{버전}:{내용해시}")
    """
    # 내용 해시 생성
    content_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()

    # 파서 버전과 내용 해시를 포함한 캐시 키 구성
    cache_key = f"render:v{parser_version}:{content_hash}"

    return cache_key
