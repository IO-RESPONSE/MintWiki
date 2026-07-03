"""Shared hosting 업그레이드 절차 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-upgrade-procedure.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_shared_hosting_upgrade_procedure_doc_exists():
    """0644 shared hosting 업그레이드 절차 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_upgrade_procedure_doc_defines_file_replacement_order():
    """파일 교체 순서와 운영 데이터 보존 기준을 명시한다."""
    content = _unwrapped_content()

    assert "파일 교체 절차" in content
    assert "`php/src/`, `php/config/*.sample`, `db/schema/`를 먼저 업로드" in content
    assert "`php/public/`을 마지막" in content
    assert "`php/vendor/`와 `php/composer.lock`을 같은 릴리스 기준으로 교체" in content
    assert "`storage/uploads/`는 새 패키지 파일로 덮어쓰지 않는다" in content


def test_shared_hosting_upgrade_procedure_doc_defines_migration_checkpoint():
    """마이그레이션 상태 확인과 실패 시 중단 기준을 고정한다."""
    content = _unwrapped_content()

    assert "마이그레이션 확인" in content
    assert "현재 schema version과 필요한 schema version" in content
    assert "shared-hosting-migration-policy.md" in content
    assert "새 코드로 트래픽을 열지 말고 maintenance mode를 유지" in content
    assert "schema version이 새 코드 요구사항보다 낮다" in content


def test_shared_hosting_upgrade_procedure_doc_defines_cache_clear_scope():
    """cache clear 대상과 삭제 금지 대상을 구분한다."""
    content = _unwrapped_content()

    assert "Cache Clear" in content
    assert "`storage/cache/`" in content
    assert "PHP opcode cache clear" in content
    assert "static asset cache purge" in content
    assert "`storage/uploads/`, `storage/logs/`, `storage/exports/`는 삭제하지 않는다" in content


def test_shared_hosting_upgrade_procedure_doc_links_related_docs():
    """관련 배포, 마이그레이션, 롤백 문서와 연결한다."""
    content = _content()

    for reference in [
        "composer-hosting-deployment.md",
        "no-composer-hosting-deployment.md",
        "shared-hosting-migration-policy.md",
        "writable-directories-policy.md",
        "php-ui-deployment-checklist.md",
        "php-ui-rollback-checklist.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
