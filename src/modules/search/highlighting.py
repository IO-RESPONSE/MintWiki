"""검색 결과 하이라이팅 자리표시자."""


def highlight_search_term(text: str, term: str) -> str:
    """
    본문 텍스트에서 질의어와 일치하는 부분을 <mark> 태그로 감싼다.

    현재는 대소문자를 구분하지 않는 단순 부분 문자열 일치만 지원하는
    자리표시자로, InMemorySearchAdapter의 검색 매칭 방식과 동일한 기준을
    사용한다. 발췌(snippet) 추출, 다중 질의어 하이라이팅, 형태소 분석
    기반 일치 등 실질적인 하이라이팅 로직은 이후 태스크에서 채워진다.

    Args:
        text: 하이라이팅을 적용할 원본 텍스트
        term: 강조할 질의어

    Returns:
        일치하는 부분마다 <mark> 태그로 감싼 텍스트. term이 비어있거나
        text 안에서 찾을 수 없으면 원본 텍스트를 그대로 반환한다.
    """
    if not term:
        return text

    lowered_text = text.lower()
    lowered_term = term.lower()
    term_length = len(term)

    pieces = []
    cursor = 0
    while True:
        match_index = lowered_text.find(lowered_term, cursor)
        if match_index == -1:
            pieces.append(text[cursor:])
            break
        pieces.append(text[cursor:match_index])
        pieces.append(f"<mark>{text[match_index:match_index + term_length]}</mark>")
        cursor = match_index + term_length

    return "".join(pieces)
