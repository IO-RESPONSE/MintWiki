"""parse_namespace 골격 함수 테스트."""
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE
from modules.acl.namespace_parser import parse_namespace


class TestParseNamespaceWithSeparator:
    """구분자가 있는 제목에서 네임스페이스를 추출하는지 확인한다."""

    def test_extracts_namespace_before_separator(self):
        assert parse_namespace("Talk:PageName") == "Talk"

    def test_strips_surrounding_whitespace_around_namespace(self):
        assert parse_namespace(" Talk : PageName") == "Talk"

    def test_only_splits_on_first_separator(self):
        assert parse_namespace("Talk:Sub:Page") == "Talk"


class TestParseNamespaceFallsBackToDefault:
    """구분자가 없거나 네임스페이스 부분이 비어있으면 기본값을 반환하는지 확인한다."""

    def test_returns_default_namespace_when_no_separator(self):
        assert parse_namespace("PageName") == DEFAULT_NAMESPACE

    def test_returns_default_namespace_when_namespace_part_is_empty(self):
        assert parse_namespace(":PageName") == DEFAULT_NAMESPACE

    def test_returns_default_namespace_when_namespace_part_is_blank(self):
        assert parse_namespace("   :PageName") == DEFAULT_NAMESPACE
