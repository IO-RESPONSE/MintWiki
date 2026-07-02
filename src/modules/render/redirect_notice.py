"""리다이렉트 공지 렌더러."""

from modules.render.escape import escape_html


def render_redirect_notice(target_page: str) -> str:
    """
    리다이렉트 공지를 HTML로 렌더링한다.

    XSS 공격을 방지하기 위해 대상 페이지명을 이스케이프한 후 링크로 감싼다.
    대상 페이지명은 사용자 입력으로 취급하여 안전하게 처리한다.

    Args:
        target_page: 리다이렉트 대상 페이지명

    Returns:
        HTML로 렌더링된 리다이렉트 공지 (화살표 기호와 함께 링크 포함)
    """
    # 대상 페이지명을 이스케이프하여 안전한 href 생성
    escaped_page = escape_html(target_page)

    # href는 URL 경로이므로, 페이지명의 특수 문자는 그대로 두고 HTML 문제는 방지
    href = f"/wiki/{escaped_page}"

    return f'<div class="redirect-notice">→ <a href="{href}">{escaped_page}</a></div>'
