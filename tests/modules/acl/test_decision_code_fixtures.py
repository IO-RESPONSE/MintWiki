"""ACL 판단 결과 코드(allow/deny/reason) 공용 fixture 기반 테스트.

`tests/modules/acl/fixtures/` 아래 교차언어 fixture(0369,
`docs/cross-language-fixture-schema.md`)를 읽어 `AclService.check()` 가
반환하는 `Decision.reason` 이 `docs/portable-exception-code-policy.md` 와
같은 `<module>.<reason>` 형식의 안정적인 code 로 고정되어 있는지 검증한다.
같은 fixture 파일을 이후 PHP 포트(0427)가 재사용한다.
"""
import json
from pathlib import Path
from typing import Optional

import jsonschema
import pytest

from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import (
    REASON_MATCHED_RULE,
    REASON_NO_MATCHING_RULE,
    AclService,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "modules" / "acl" / "fixtures"
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "acl" / "manifest.json"
SCHEMA_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "schema" / "cross_language_fixture.schema.json"
)

FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_rule(data: dict) -> Rule:
    return Rule(
        id=data["id"],
        subject_type=SubjectType(data["subject_type"]),
        permission=Permission(data["permission"]),
        effect=Effect(data["effect"]),
        subject_id=data.get("subject_id"),
    )


def _build_document_acl(data: Optional[dict]) -> Optional[DocumentAcl]:
    if data is None:
        return None
    return DocumentAcl(
        document_id=data["document_id"],
        rules=[_build_rule(rule) for rule in data.get("rules", [])],
    )


def test_fixtures_directory_matches_manifest():
    """manifest.json 의 fixtures.path/format 이 실제 디렉터리와 일치한다."""
    manifest = _load_json(MANIFEST_PATH)
    assert manifest["fixtures"]["path"] == "tests/modules/acl/fixtures"
    assert manifest["fixtures"]["format"] == "json"


def test_fixtures_directory_is_not_empty():
    """fixture 가 최소 1개 이상 채워져 있다."""
    assert FIXTURE_FILES


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_fixture_conforms_to_cross_language_schema(fixture_path):
    """각 fixture 파일이 교차언어 fixture JSON Schema를 만족한다."""
    schema = _load_json(SCHEMA_PATH)
    data = _load_json(fixture_path)
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_check_matches_fixture(fixture_path):
    """AclService.check() 의 실제 결과가 fixture 의 expected 와 일치한다."""
    data = _load_json(fixture_path)
    input_ = data["input"]
    assert data["errors"] == []

    service = AclService()
    decision = service.check(
        permission=Permission(input_["permission"]),
        subject_type=SubjectType(input_["subject_type"]),
        subject_id=input_.get("subject_id"),
        document_acl=_build_document_acl(input_.get("document_acl")),
        namespace=input_.get("namespace", DEFAULT_NAMESPACE),
    )

    expected = data["expected"]
    assert decision.allowed == expected["allowed"]
    assert decision.reason == expected["reason"]
    assert decision.matched_rule_id == expected["matched_rule_id"]


class TestDecisionReasonCodesAreStable:
    """fixture 가 쓰는 reason code 가 언어 독립 code 형식을 따르는지 확인한다."""

    def test_fixtures_only_use_the_two_declared_reason_codes(self):
        reasons = {_load_json(path)["expected"]["reason"] for path in FIXTURE_FILES}
        assert reasons == {REASON_MATCHED_RULE, REASON_NO_MATCHING_RULE}

    def test_reason_codes_follow_module_dot_reason_format(self):
        for reason in (REASON_MATCHED_RULE, REASON_NO_MATCHING_RULE):
            assert reason.startswith("acl.")
            assert reason == reason.lower()
