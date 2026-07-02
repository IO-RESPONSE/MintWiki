"""Repository 트랜잭션 정책 문서(0473)를 검증한다.

docs/repository-transaction-policy.md가 db-adapter-contract.md §2가 미뤄둔
commit/rollback 시점과 크로스 모듈 트랜잭션 경계를, 실제 코드(repository.py,
transaction.py)의 패턴에 맞게 문서화했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "repository-transaction-policy.md"


def test_repository_transaction_policy_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/repository-transaction-policy.md should exist"


def test_repository_transaction_policy_doc_defines_commit_rollback_order():
    """commit/rollback의 정확한 순서(add/execute -> flush -> commit, 실패 시 rollback)를 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "flush()" in content
    assert "commit()" in content
    assert "rollback()" in content


def test_repository_transaction_policy_doc_defines_cross_module_boundary():
    """크로스 모듈 원자적 쓰기는 개별 저장소 create를 순서대로 호출하지 않고
    전용 트랜잭션 헬퍼를 쓴다는 규칙을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "DocumentRevisionTransaction" in content
    assert "부분 쓰기" in content


def test_repository_transaction_policy_doc_aligns_python_and_php_commit_points():
    """Python AsyncSession과 PHP PDO의 commit 경계를 맞추는 절이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "PDO" in content
    assert "beginTransaction" in content
    assert "PDOException" in content


def test_repository_transaction_policy_doc_links_to_related_policy_docs():
    """이 문서가 기존 DB adapter 계약/persistence 경계 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "db-adapter-contract.md" in content
    assert "persistence-boundaries.md" in content


def test_db_adapter_contract_doc_links_to_transaction_policy_doc():
    """db-adapter-contract.md가 자신이 미뤄둔 0473 문서를 실제 파일로 연결하는지 확인한다."""
    contract_path = Path(__file__).parent.parent / "docs" / "db-adapter-contract.md"
    content = contract_path.read_text()

    assert "repository-transaction-policy.md" in content
