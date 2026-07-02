"""document 모듈 예외의 안정적인 error code 를 검증한다.

`docs/portable-exception-code-policy.md` 가 정한 `<module>.<reason>` 형식과
`tests/modules/document/fixtures` 의 `errors` 필드가 참조하는 code 문자열이
실제 예외 클래스의 `code` 속성과 일치하는지 확인한다.
"""
from modules.document.repository import (
    DocumentNotFoundError,
    DuplicateNormalizedTitleError,
)
from modules.document.title import EmptyTitleError


class TestDocumentErrorCodes:
    """document 모듈 예외 클래스의 code 속성 테스트."""

    def test_empty_title_error_code(self):
        """EmptyTitleError 는 document.empty_title code 를 노출한다."""
        assert EmptyTitleError.code == "document.empty_title"

    def test_duplicate_normalized_title_error_code(self):
        """DuplicateNormalizedTitleError 는 document.duplicate_title code 를 노출한다."""
        assert DuplicateNormalizedTitleError.code == "document.duplicate_title"

    def test_document_not_found_error_code(self):
        """DocumentNotFoundError 는 document.not_found code 를 노출한다."""
        assert DocumentNotFoundError.code == "document.not_found"

    def test_code_is_accessible_from_instance(self):
        """code 는 클래스 속성이므로 인스턴스에서도 조회할 수 있다."""
        assert EmptyTitleError("제목은 비어있을 수 없습니다").code == "document.empty_title"
        assert DuplicateNormalizedTitleError("중복").code == "document.duplicate_title"
        assert DocumentNotFoundError("없음").code == "document.not_found"

    def test_all_codes_are_unique(self):
        """document 모듈의 code 는 예외 클래스마다 유일하다."""
        codes = {
            EmptyTitleError.code,
            DuplicateNormalizedTitleError.code,
            DocumentNotFoundError.code,
        }
        assert len(codes) == 3

    def test_all_codes_share_document_module_prefix(self):
        """document 모듈의 모든 code 는 'document.' 접두사를 가진다."""
        for code in (
            EmptyTitleError.code,
            DuplicateNormalizedTitleError.code,
            DocumentNotFoundError.code,
        ):
            assert code.startswith("document.")
