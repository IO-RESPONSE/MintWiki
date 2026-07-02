"""Portable duplicate key handling 문서(0474)를 검증한다.

docs/portable-duplicate-key-handling.md가 db-adapter-contract.md §3가 미뤄둔
제약 위반 식별 방법을, DB별 오류 메시지 문자열 매칭을 금지하고 SQLSTATE/제약
이름 기반으로 확정했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "portable-duplicate-key-handling.md"


def test_portable_duplicate_key_handling_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/portable-duplicate-key-handling.md should exist"


def test_portable_duplicate_key_handling_doc_forbids_error_message_matching():
    """DB별 오류 메시지 문자열 매칭을 명시적으로 금지하는지 확인한다."""
    content = _doc_path().read_text()

    assert "금지" in content
    assert "str(e)" in content
    assert '"normalized_title" in str(e)' in content


def test_portable_duplicate_key_handling_doc_defines_sqlstate_based_detection():
    """유일성 위반 판별 기준으로 SQLSTATE/errno를 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "SQLSTATE" in content
    assert "23505" in content
    assert "1062" in content
    assert "errorInfo" in content


def test_portable_duplicate_key_handling_doc_maps_constraint_name_to_domain_error():
    """제약 이름(uq_<table>_<column>) 기반 도메인 예외 매핑을 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "uq_document_normalized_title" in content
    assert "DuplicateNormalizedTitleError" in content
    assert "portable-schema-naming-policy.md" in content


def test_portable_duplicate_key_handling_doc_links_to_related_policy_docs():
    """이 문서가 기존 DB adapter 계약/트랜잭션 정책 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "db-adapter-contract.md" in content
    assert "repository-transaction-policy.md" in content


def test_db_adapter_contract_doc_links_to_duplicate_key_handling_doc():
    """db-adapter-contract.md가 자신이 미뤄둔 0474 문서를 실제 파일로 연결하는지 확인한다."""
    contract_path = Path(__file__).parent.parent / "docs" / "db-adapter-contract.md"
    content = contract_path.read_text()

    assert "portable-duplicate-key-handling.md" in content
