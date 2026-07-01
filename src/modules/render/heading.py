"""제목 렌더러."""
import re
from modules.render.escape import escape_html


def generate_heading_id(text: str) -> str:
    """
    제목 텍스트로부터 id 속성 값을 생성한다.

    HTML id 속성 규칙을 따르며, 공백은 하이픈으로 변환하고 특수 문자는 제거한다.

    Args:
        text: 제목 텍스트

    Returns:
        HTML id 속성으로 사용할 수 있는 슬러그 문자열
    """
    if not text or not text.strip():
        return ""

    # 소문자로 변환
    slug = text.lower()

    # 공백을 하이픈으로 변환
    slug = re.sub(r'\s+', '-', slug)

    # 영문, 숫자, 하이픈만 유지 (기타 특수 문자 제거)
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # 연속된 하이픈을 하나로 축약
    slug = re.sub(r'-+', '-', slug)

    # 앞뒤 하이픈 제거
    slug = slug.strip('-')

    return slug


def render_heading(level: int, content: str) -> str:
    """
    제목을 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 내용을 이스케이프한 후 id 속성을 추가하여 렌더링한다.

    Args:
        level: 제목 레벨 (1-6)
        content: 제목의 텍스트 내용

    Returns:
        HTML로 렌더링된 제목 ('<h{level} id="{id}">...</h{level}>' 형태)
    """
    # 제목 레벨 검증 (1-6이 표준)
    if not isinstance(level, int) or level < 1 or level > 6:
        level = 1

    escaped_content = escape_html(content)
    heading_id = generate_heading_id(content)

    # id가 있으면 id 속성 추가, 없으면 id 속성 없이 렌더링
    if heading_id:
        return f'<h{level} id="{heading_id}">{escaped_content}</h{level}>'
    else:
        return f'<h{level}>{escaped_content}</h{level}>'
