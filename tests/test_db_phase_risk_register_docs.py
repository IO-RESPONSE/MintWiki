"""DB phase risk register 문서(0499)를 검증한다.

docs/db-phase-risk-register.md가 collation, transaction, migration
세 가지 위험 영역을 식별하고, 각각의 영향 범위와 완화 전략을 정의했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "db-phase-risk-register.md"


def test_db_phase_risk_register_doc_exists():
    """위험 관리 문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/db-phase-risk-register.md should exist"


def test_db_phase_risk_register_doc_identifies_collation_risks():
    """collation 위험(문자 비교 방식 불일치, 한글/이모지 저장)을 식별하는지 확인한다."""
    content = _doc_path().read_text()

    # 위험 식별
    assert "1. Collation 위험" in content
    assert "문자 비교 방식 불일치" in content
    assert "한글/이모지 문자셋 오류" in content

    # PostgreSQL과 MariaDB 차이점 명시
    assert "PostgreSQL" in content
    assert "MariaDB" in content
    assert "utf8mb4_bin" in content or "collation" in content


def test_db_phase_risk_register_doc_describes_collation_impact():
    """collation 위험의 영향 범위를 기술했는지 확인한다."""
    content = _doc_path().read_text()

    # UNIQUE 제약 위반 등 구체적 시나리오
    assert "UNIQUE 제약" in content
    assert "쿼리 결과 차이" in content or "쿼리" in content
    assert "대소문자" in content


def test_db_phase_risk_register_doc_identifies_transaction_risks():
    """transaction 위험(DDL 암묵적 커밋, 격리 수준 차이, 경계 위반)을 식별하는지 확인한다."""
    content = _doc_path().read_text()

    # 위험 식별
    assert "2. Transaction 위험" in content
    assert "DDL 암묵적 커밋" in content
    assert "격리 수준 차이" in content
    assert "트랜잭션 경계 위반" in content


def test_db_phase_risk_register_doc_describes_ddl_implicit_commit():
    """DDL 암묵적 커밋 위험의 영향과 완화 방법을 기술했는지 확인한다."""
    content = _doc_path().read_text()

    # 영향
    assert "부분 마이그레이션" in content or "부분" in content
    assert "스키마 불일치" in content

    # 완화
    assert "마이그레이션 분산" in content or "별도 파일" in content
    assert "멱등성" in content or "IF NOT EXISTS" in content


def test_db_phase_risk_register_doc_describes_isolation_level_risk():
    """격리 수준 차이 위험의 phantom read 등을 기술했는지 확인한다."""
    content = _doc_path().read_text()

    # READ COMMITTED vs REPEATABLE READ 차이점
    assert "READ COMMITTED" in content or "격리 수준" in content
    assert "phantom" in content or "Phantom" in content
    assert "REPEATABLE READ" in content


def test_db_phase_risk_register_doc_identifies_migration_risks():
    """migration 위험(버전 불일치, FK 순서, 네이밍 충돌)을 식별하는지 확인한다."""
    content = _doc_path().read_text()

    # 위험 식별
    assert "3. Migration 위험" in content
    assert "스키마 버전 불일치" in content
    assert "외래키 제약 순서 위반" in content
    assert "네이밍 충돌" in content or "마이그레이션 파일 네이밍" in content


def test_db_phase_risk_register_doc_describes_schema_version_risk():
    """스키마 버전 불일치 위험의 이식 실패 등을 기술했는지 확인한다."""
    content = _doc_path().read_text()

    # 영향
    assert "이식 불가" in content or "이식" in content
    assert "운영 중 혼선" in content or "혼선" in content

    # 완화
    assert "체크리스트" in content
    assert "스키마 다이제스트" in content or "스키마" in content


def test_db_phase_risk_register_doc_defines_remediation_strategies():
    """각 위험에 대한 구체적인 완화 전략(예: 명시적 collation, 트랜잭션 헬퍼)을 정의했는지 확인한다."""
    content = _doc_path().read_text()

    # Collation 완화
    assert "COLLATE utf8mb4_bin" in content or "collation을 명시" in content

    # Transaction 완화
    assert "DocumentRevisionTransaction" in content
    assert "명시적 격리 수준" in content or "격리 수준" in content

    # Migration 완화
    assert "Migration Portability Checklist" in content or "체크리스트" in content


def test_db_phase_risk_register_doc_provides_test_examples():
    """각 위험 항목이 검증 가능한 테스트 케이스를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    # Python 테스트 코드 예제 포함
    assert "def test_" in content
    assert "assert" in content


def test_db_phase_risk_register_doc_links_to_policy_docs():
    """위험 관리 문서가 기존 정책 문서들(collation, transaction, migration policy)과 연결되는지 확인한다."""
    content = _doc_path().read_text()

    # 주요 정책 문서 참조
    assert "Portable Text Collation Policy" in content
    assert "Repository Transaction Policy" in content
    assert "Migration Portability Checklist" in content
    assert "portable-text-collation-policy.md" in content
    assert "repository-transaction-policy.md" in content
    assert "migration-portability-checklist.md" in content


def test_db_phase_risk_register_doc_specifies_verification_methods():
    """각 위험에 대해 자동 검사/수동 리뷰/테스트 방법을 구분해서 명시하는지 확인한다."""
    content = _doc_path().read_text()

    # 검증 방법 명시
    assert "자동 검사" in content or "자동" in content
    assert "수동 리뷰" in content or "수동" in content
    assert "테스트 케이스" in content or "테스트" in content


def test_db_phase_risk_register_doc_includes_integration_validation_strategy():
    """종합 검증 전략(로컬 검증, 코드 리뷰, CI/CD 단계별)을 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "4. 종합 검증 전략" in content or "종합" in content
    assert "로컬 검증" in content or "로컬" in content
    assert "코드 리뷰 체크리스트" in content or "리뷰" in content
    assert "CI/CD" in content


def test_db_phase_risk_register_doc_aligns_with_phase_scope():
    """문서가 Phase C(0441-0520) 범위에 맞는 위험만 식별했는지 확인한다."""
    content = _doc_path().read_text()

    # Phase C 명시
    assert "Phase C" in content
    assert "0441-0520" in content

    # Phase C 외부 범위는 포함하지 않음 (네트워크, 성능, 비즈니스 로직 등)
    assert "성능" not in content or ("성능" in content and "Phase D" in content)
