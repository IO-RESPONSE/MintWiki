"""ACL 매트릭스 픽스처 로더와 픽스처 형식을 검증한다."""
import pytest

from modules.acl.matrix_fixture import (
    AclMatrixCase,
    AclMatrixFixture,
    AclMatrixFixtureLoader,
)
from modules.acl.matrix_runner import AclMatrixRunner
from modules.acl.rule import Rule


class TestAclMatrixFixtureLoaderLoadAll:
    """load_all이 반환하는 픽스처 목록의 형식을 검증한다."""

    def test_loads_all_fixtures(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        assert len(fixtures) > 0

    def test_returns_list_of_acl_matrix_fixtures(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        assert all(isinstance(f, AclMatrixFixture) for f in fixtures)

    def test_fixture_names_are_unique(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        names = [f.name for f in fixtures]
        assert len(names) == len(set(names))

    def test_each_fixture_has_rules_and_cases(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        for fixture in fixtures:
            assert fixture.name
            assert all(isinstance(rule, Rule) for rule in fixture.rules)
            assert len(fixture.cases) > 0
            assert all(isinstance(c, AclMatrixCase) for c in fixture.cases)


class TestAclMatrixFixtureLoaderLoadByName:
    """load_by_name이 이름으로 픽스처를 조회하는 동작을 검증한다."""

    def test_loads_known_fixture(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        assert fixture.name == "public_read_only"

    def test_raises_error_for_unknown_fixture(self):
        with pytest.raises(ValueError, match="Unknown fixture"):
            AclMatrixFixtureLoader.load_by_name("nonexistent_fixture")


class TestAclMatrixFixtureDocumentAcl:
    """AclMatrixFixture.document_acl이 픽스처 규칙으로 DocumentAcl을 구성하는지 검증한다."""

    def test_document_acl_contains_fixture_rules(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        document_acl = fixture.document_acl()
        assert document_acl.rules() == fixture.rules


class TestAclMatrixFixturesAgainstAclService:
    """모든 매트릭스 픽스처의 각 케이스가 AclService의 실제 판단과 일치하는지 검증한다."""

    @pytest.mark.parametrize(
        "fixture", AclMatrixFixtureLoader.load_all(), ids=lambda f: f.name
    )
    def test_all_cases_match_expected_decision(self, fixture):
        runner = AclMatrixRunner()

        results = runner.run_fixture(fixture)

        failing = [result.describe() for result in results if not result.passed()]
        assert failing == []
