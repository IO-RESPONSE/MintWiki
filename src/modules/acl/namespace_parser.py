"""문서 제목에서 네임스페이스를 추출하는 파싱 유틸리티."""
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE

NAMESPACE_SEPARATOR = ":"


def parse_namespace(title: str) -> str:
    """
    문서 제목에서 네임스페이스 부분만 추출하는 골격이다.

    "네임스페이스:제목" 형태의 문자열에서 첫 번째 구분자(":") 앞부분을
    네임스페이스로 취급한다. 구분자가 없거나 구분자 앞부분이 공백뿐이면
    DEFAULT_NAMESPACE를 반환한다. 제목 정규화나 알려진 네임스페이스 목록
    검증 같은 세부 로직은 이후 태스크에서 채워진다.

    Args:
        title: 네임스페이스를 추출할 원본 제목

    Returns:
        추출된 네임스페이스, 없으면 DEFAULT_NAMESPACE
    """
    namespace, separator, _ = title.partition(NAMESPACE_SEPARATOR)
    namespace = namespace.strip()

    if not separator or not namespace:
        return DEFAULT_NAMESPACE

    return namespace
