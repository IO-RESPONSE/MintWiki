"""Portable search DB boundary 문서(0479)를 검증한다.

docs/portable-search-db-boundary.md가 DB 계층과 search 모듈 사이의 경계 —
저장소는 검색 질의를 직접 실행하지 않고, DB fallback adapter 내부도 벤더
전문 검색 문법을 쓰지 않으며, capability.py의 supports_fulltext 플래그가
검색 경로 분기에 쓰이지 않는다는 것 — 을 확정했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "portable-search-db-boundary.md"


def test_portable_search_db_boundary_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/portable-search-db-boundary.md should exist"


def test_doc_forbids_repository_from_running_search_queries_directly():
    """DB 계층(Database* 저장소)이 검색 질의를 직접 실행하지 않는다는 규칙을 확인한다."""
    content = _doc_path().read_text()

    assert "검색 질의" in content
    assert "SearchAdapter" in content
    assert "직접 실행하지 않는다" in content


def test_doc_keeps_vendor_fulltext_syntax_out_of_fallback_adapter():
    """DB fallback adapter 내부에서도 벤더 전문 검색 문법을 금지하는지 확인한다."""
    content = _doc_path().read_text()

    assert "tsvector" in content
    assert "tsquery" in content
    assert "MATCH ... AGAINST" in content
    assert "shingle" in content


def test_doc_pins_supports_fulltext_flag_as_informational_only():
    """capability.py의 supports_fulltext 플래그가 검색 경로 분기에 쓰이지 않는다는 규칙을 확인한다."""
    content = _doc_path().read_text()

    assert "supports_fulltext" in content
    assert "capability.py" in content


def test_doc_links_to_related_boundary_docs():
    """이 문서가 기존 ANSI SQL 정책/DB adapter 계약/search adapter 설계 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "ansi-sql-persistence-policy.md" in content
    assert "db-adapter-contract.md" in content
    assert "search-adapter-design.md" in content
    assert "persistence-boundaries.md" in content


def test_doc_does_not_schedule_fallback_adapter_implementation_in_this_phase():
    """DB fallback adapter의 실제 구현은 이 Phase 큐에 없다고 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "later queue" in content
