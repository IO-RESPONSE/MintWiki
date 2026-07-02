"""URL 새니타이저."""

from typing import Optional


# 안전한 URL 스킴 목록
SAFE_SCHEMES = {
    "http",
    "https",
    "ftp",
    "ftps",
    "mailto",
    "tel",
    "sms",
    "geo",
}


def sanitize_url(url: str) -> Optional[str]:
    """
    URL을 새니타이즈하여 XSS 및 기타 보안 위협을 방지한다.

    안전하지 않은 스킴(javascript:, data:, vbscript: 등)으로 시작하는 URL을 필터링한다.
    상대 경로는 안전한 것으로 간주한다.

    Args:
        url: 새니타이즈할 URL

    Returns:
        안전한 URL이면 원본 URL, 안전하지 않으면 None
    """
    if not url:
        return url

    # 스킴이 있는지 확인하기 위해 콜론을 찾음
    colon_index = url.find(":")
    if colon_index == -1:
        # 스킴이 없으면 상대 경로이므로 안전
        return url

    # URL 스킴 추출 (콜론 이전 부분)
    # URL에서 스킴은 알파벳, 숫자, +, -, . 등으로 구성됨
    scheme = url[:colon_index].lower().strip()

    # 스킴에 공백이 있으면 안전하지 않은 시도로 간주
    if " " in scheme or "\t" in scheme or "\n" in scheme:
        return None

    # 안전한 스킴인지 확인
    if scheme in SAFE_SCHEMES:
        return url

    # 안전하지 않은 스킴
    return None
