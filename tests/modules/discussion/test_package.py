"""discussion 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.discussion


def test_discussion_package_is_importable():
    assert modules.discussion.__doc__ == "Discussion module package."


def test_discussion_package_exports_are_empty_initially():
    # 후속 태스크에서 스레드/댓글 등의 모델이 추가되면 __all__에 채워진다.
    assert modules.discussion.__all__ == []
