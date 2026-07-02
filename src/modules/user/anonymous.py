"""익명 아이덴티티 도메인 모델."""


class AnonymousIdentity:
    """
    로그인하지 않은 방문자를 나타내는 도메인 모델.

    User와 달리 계정 식별자나 사용자명을 가지지 않으며, 권한 검사에서
    로그인 여부를 구분하기 위한 표식으로 사용된다.
    """

    is_anonymous = True

    def __repr__(self) -> str:
        return "AnonymousIdentity()"
