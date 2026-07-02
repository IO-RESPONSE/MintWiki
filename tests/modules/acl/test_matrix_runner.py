"""ACL 매트릭스 러너의 동작을 검증한다."""
from modules.acl.matrix_fixture import AclMatrixFixtureLoader
from modules.acl.matrix_runner import AclMatrixCaseResult, AclMatrixRunner
from modules.acl.service import AclService


class TestAclMatrixRunnerRunFixture:
    """run_fixture가 픽스처의 각 케이스를 실행하고 결과를 반환하는지 검증한다."""

    def test_returns_one_result_per_case(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        runner = AclMatrixRunner()

        results = runner.run_fixture(fixture)

        assert len(results) == len(fixture.cases)
        assert all(isinstance(result, AclMatrixCaseResult) for result in results)

    def test_results_pass_for_a_correct_fixture(self):
        fixture = AclMatrixFixtureLoader.load_by_name("owner_user_allowed_others_denied")
        runner = AclMatrixRunner()

        results = runner.run_fixture(fixture)

        assert all(result.passed() for result in results)

    def test_result_carries_fixture_name_and_matched_rule(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        runner = AclMatrixRunner()

        results = runner.run_fixture(fixture)

        assert all(result.fixture_name == "public_read_only" for result in results)
        allow_result = next(r for r in results if r.case.expected_matched_rule_id)
        assert allow_result.actual_matched_rule_id == "all-read-allow"

    def test_uses_injected_service(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        service = AclService()
        runner = AclMatrixRunner(service=service)

        runner.run_fixture(fixture)

        assert runner.service is service


class TestAclMatrixRunnerRunAll:
    """run_all이 여러 픽스처의 케이스를 모두 실행하는지 검증한다."""

    def test_returns_results_for_every_fixture(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        runner = AclMatrixRunner()

        results = runner.run_all(fixtures)

        expected_count = sum(len(fixture.cases) for fixture in fixtures)
        assert len(results) == expected_count

    def test_all_bundled_fixtures_pass(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        runner = AclMatrixRunner()

        results = runner.run_all(fixtures)

        failing = [result.describe() for result in results if not result.passed()]
        assert failing == []


class TestAclMatrixRunnerFailures:
    """failures가 기대값과 어긋난 결과만 골라내는지 검증한다."""

    def test_returns_empty_list_when_everything_matches(self):
        fixtures = AclMatrixFixtureLoader.load_all()
        runner = AclMatrixRunner()

        assert runner.failures(fixtures) == []

    def test_detects_mismatch_against_a_broken_service(self):
        class AlwaysDenyDecision:
            matched_rule_id = None

            def is_allowed(self):
                return False

        class AlwaysDenyService:
            def check(self, **kwargs):
                return AlwaysDenyDecision()

        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        runner = AclMatrixRunner(service=AlwaysDenyService())

        failures = runner.failures([fixture])

        assert len(failures) > 0
        assert all(not result.passed() for result in failures)


class TestAclMatrixCaseResultPassed:
    """AclMatrixCaseResult.passed의 판정 로직을 검증한다."""

    def test_fails_when_allowed_differs(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        case = fixture.cases[0]

        result = AclMatrixCaseResult(
            fixture_name=fixture.name,
            case=case,
            actual_allowed=not case.expected_allowed,
            actual_matched_rule_id=case.expected_matched_rule_id,
        )

        assert result.passed() is False

    def test_fails_when_matched_rule_differs(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        case = fixture.cases[0]

        result = AclMatrixCaseResult(
            fixture_name=fixture.name,
            case=case,
            actual_allowed=case.expected_allowed,
            actual_matched_rule_id="unexpected-rule",
        )

        assert result.passed() is False

    def test_passes_when_expected_matched_rule_is_none(self):
        fixture = AclMatrixFixtureLoader.load_by_name("group_edit_with_anonymous_read_denied")
        case = next(c for c in fixture.cases if c.expected_matched_rule_id is None)

        result = AclMatrixCaseResult(
            fixture_name=fixture.name,
            case=case,
            actual_allowed=case.expected_allowed,
            actual_matched_rule_id=None,
        )

        assert result.passed() is True

    def test_describe_mentions_fixture_and_subject(self):
        fixture = AclMatrixFixtureLoader.load_by_name("public_read_only")
        case = fixture.cases[0]

        result = AclMatrixCaseResult(
            fixture_name=fixture.name,
            case=case,
            actual_allowed=case.expected_allowed,
            actual_matched_rule_id=case.expected_matched_rule_id,
        )

        assert fixture.name in result.describe()
