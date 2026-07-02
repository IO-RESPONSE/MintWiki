"""CSS 값 새니타이저."""

from typing import Optional
import re


# 위험한 CSS 키워드 패턴
DANGEROUS_CSS_KEYWORDS = {
    "expression",  # IE에서의 XSS
    "behavior",    # IE에서의 XSS
    "@import",     # 외부 리소스 로드
    "@-moz-",      # Mozilla 특정 규칙
    "@-webkit-",   # WebKit 특정 규칙
    "@-ms-",       # Microsoft 특정 규칙
    "@keyframes",  # 애니메이션 정의
    "javascript",  # javascript: URL
    "data",        # data: URL (제한적)
    "vbscript",    # VBScript URL
    "-moz-binding", # Mozilla 바인딩 XSS
}

# 위험한 CSS 함수 패턴
DANGEROUS_CSS_FUNCTIONS = {
    "expression",     # IE
    "url",            # URL 함수 - javascript: 또는 data:를 포함할 수 있음
    "var",            # CSS 변수 - 동적 스타일 우회 시도
}


def is_safe_css_value(value: str) -> bool:
    """
    CSS 값이 안전한지 확인한다.

    XSS 공격을 방지하기 위해 위험한 CSS 키워드와 함수를 필터링한다.

    Args:
        value: 확인할 CSS 값

    Returns:
        안전한 CSS 값이면 True
    """
    if not value:
        return True

    value_lower = value.lower()

    # 위험한 키워드 확인
    for keyword in DANGEROUS_CSS_KEYWORDS:
        if keyword in value_lower:
            return False

    # 위험한 함수 패턴 확인 (url, expression, var 등)
    for func in DANGEROUS_CSS_FUNCTIONS:
        # url() 함수에서 javascript: 또는 data: URL 확인
        if func == "url":
            url_pattern = r"url\s*\(\s*['\"]?(?:javascript|data|vbscript):"
            if re.search(url_pattern, value_lower):
                return False
        else:
            # expression() 또는 var() 같은 함수 패턴
            func_pattern = rf"{func}\s*\("
            if re.search(func_pattern, value_lower):
                return False

    # 유니코드 이스케이프를 통한 우회 시도 확인
    # \0 또는 \00 형태의 null 바이트 (뒤에 공백이 있거나 끝에 있을 수 있음)
    if re.search(r"\\0{1,6}(?:\s|$)", value_lower):
        return False

    # CSS 주석 내에서 위험한 패턴이 숨겨져 있을 수 있음
    if "/*" in value_lower or "*/" in value_lower:
        return False

    return True


def sanitize_css_value(value: str) -> Optional[str]:
    """
    CSS 값을 새니타이즈하여 XSS 및 기타 보안 위협을 방지한다.

    위험한 CSS 키워드, 함수, URL 스킴을 필터링한다.

    Args:
        value: 새니타이즈할 CSS 값

    Returns:
        안전한 CSS 값이면 원본 값, 안전하지 않으면 None
    """
    if not value:
        return value

    if is_safe_css_value(value):
        return value

    return None
