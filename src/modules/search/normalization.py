"""한국어 텍스트 정규화 자리표시자."""
import unicodedata


def normalize_korean_text(text: str) -> str:
    """
    한국어 검색어/본문 텍스트를 정규화한다.

    현재는 유니코드 NFC 정규화만 수행하는 자리표시자로, 자모가 분리되어
    입력된 한글(초성/중성/종성 낱자모)을 완성형 음절로 합쳐 어댑터 간
    비교가 일관되도록 한다. 조사/어미 제거, 초성 검색 지원 등 실질적인
    한국어 형태소 분석은 이후 태스크에서 채워진다.

    Args:
        text: 정규화할 원본 텍스트

    Returns:
        유니코드 NFC 정규화가 적용된 텍스트
    """
    return unicodedata.normalize("NFC", text)
