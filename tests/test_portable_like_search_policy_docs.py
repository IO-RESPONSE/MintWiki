"""Portable LIKE search policy 문서(0512)를 검증한다.

docs/portable-like-search-policy.md가 ILIKE 금지와 두 가지 대안(정규화 컬럼,
함수 기반 비교)을 명시하고, 각 정책의 적용 시점을 구분했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "portable-like-search-policy.md"


def test_portable_like_search_policy_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/portable-like-search-policy.md should exist"


def test_doc_forbids_ilike():
    """ILIKE 연산자 금지를 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "ILIKE" in content
    assert "대소문자를 무시한" in content or "대소문자 무시" in content
    assert "금지" in content or "쓰지 않는다" in content


def test_doc_defines_three_policies():
    """세 가지 정책이 명시되는지 확인한다."""
    content = _doc_path().read_text()

    assert "정책 1" in content
    assert "정책 2" in content
    assert "정책 3" in content

    # 정책 1: 정규화 컬럼
    assert "정규화된 컬럼" in content or "normalized" in content

    # 정책 2: LOWER() 함수
    assert "LOWER()" in content or "함수 기반" in content

    # 정책 3: Collation 변경
    assert "collation" in content or "utf8mb4" in content


def test_doc_explains_normalized_column_approach():
    """정책 1 (정규화 컬럼)의 설명이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "정규화된 컬럼" in content
    assert "normalized_title" in content
    assert "원본 컬럼" in content or "원본" in content
    assert "소문자" in content
    assert "인덱스" in content or "성능" in content


def test_doc_explains_lower_function_approach():
    """정책 2 (함수 기반)의 설명이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "LOWER()" in content
    assert "LIKE" in content
    assert "함수" in content or "함수를" in content
    assert "스키마 변경" in content


def test_doc_explains_collation_approach_with_warnings():
    """정책 3 (collation 변경)의 설명과 경고가 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "collation" in content
    assert "utf8mb4_general_ci" in content or "utf8mb4_unicode_ci" in content
    assert "경고" in content or "주의" in content or "마지막 수단" in content
    assert "동일하지 않을 수 있다" in content or "부작용" in content


def test_doc_provides_selection_criteria():
    """세 정책 간 선택 기준이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "선택 기준" in content or "권장 정책" in content
    # 테이블 형식으로 정리되어 있어야 함
    assert "상황" in content or "언제" in content


def test_doc_includes_examples():
    """각 정책의 예시 코드가 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "예시" in content or "예" in content
    # 파이썬 코드 예시
    assert "def " in content or "async def" in content
    # 정규화 검색 예시
    assert "normalized_title" in content


def test_doc_links_to_related_documents():
    """관련 문서(ANSI SQL 정책, text collation 정책)와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "ansi-sql-persistence-policy.md" in content
    assert "portable-text-collation-policy.md" in content
    assert "persistence-boundaries.md" in content
    assert "search-adapter-design.md" in content


def test_doc_defines_scope():
    """이 정책이 적용되는 범위를 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "적용 범위" in content or "응용" in content or "Scope" in content
    assert "repository.py" in content or "저장소" in content
    assert "service.py" in content or "서비스" in content


def test_doc_notes_existing_examples():
    """기존 코드(document.normalized_title)에서 패턴이 이미 사용되는지 언급하는지 확인한다."""
    content = _doc_path().read_text()

    assert "document.normalized_title" in content
    assert "이미" in content or "기존" in content


def test_doc_mentions_ansi_sql_compatibility():
    """LOWER() 함수와 LIKE의 ANSI SQL 호환성을 언급하는지 확인한다."""
    content = _doc_path().read_text()

    assert "ANSI" in content
    assert "표준" in content or "호환" in content
    assert "PostgreSQL" in content
    assert "MariaDB" in content


def test_doc_distinguishes_from_fulltext_search():
    """전문 검색과의 구분이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "전문 검색" in content or "full-text" in content
    assert "search-adapter" in content or "SearchAdapter" in content


def test_doc_mentions_future_tasks():
    """0447, 0479 등 후속 작업을 언급하는지 확인한다."""
    content = _doc_path().read_text()

    assert "0447" in content or "0479" in content or "이 문서 이후 단계" in content


def test_doc_follows_phase_c_header():
    """Phase C 문서의 헤더 형식을 따르는지 확인한다."""
    content = _doc_path().read_text()

    assert "Phase C" in content
    assert "0441-0520" in content
    assert "ANSI SQL" in content


def test_doc_is_self_contained():
    """문서 제목부터 관련 문서까지 자체 완결되는지 확인한다."""
    content = _doc_path().read_text()

    # 시작: 제목
    assert content.startswith("# Portable LIKE Search Policy")

    # 중간: 목적/범위/정책
    assert "목적" in content
    assert "적용 범위" in content

    # 끝: 관련 문서
    assert "관련 문서" in content
