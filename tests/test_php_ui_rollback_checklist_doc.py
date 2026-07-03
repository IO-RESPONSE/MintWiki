"""`docs/php-ui-rollback-checklist.md` 가 태스크 0609 의 목표("UI rollback 체크리스트를 추가한다")
와 Notes 요구사항("schema/UI 호환성을 다룬다")을 실제로 고정하고 있으며,
그 체크리스트가 가리키는 문서/스크립트가 실제로 존재하고 서로 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-ui-rollback-checklist.md"

REQUIRED_DOC_HEADINGS = [
    "## 사용법",
    "## 1. 롤백 전 상태 파악 (Pre-Rollback Assessment)",
    "## 2. 롤백 범위 결정 (Rollback Scope Decision)",
    "## 3. 롤백 계획 수립 (Rollback Plan)",
    "## 4. 롤백 실행 (Rollback Execution)",
    "## 5. 롤백 후 검증 (Post-Rollback Verification)",
    "## 6. 롤백 후 지속적 모니터링 (Post-Rollback Monitoring)",
    "## 7. 롤백 후 근본 원인 분석 (RCA)",
    "## 8. 이 체크리스트가 다루지 않는 것",
    "## 관련 문서",
]

REQUIRED_SUBSECTIONS = [
    "### 1.1 오류 신호와 영향도 평가",
    "### 1.2 배포된 변경사항 확인",
    "### 1.3 Schema/UI 호환성 확인",
    "### 2.1 UI만 롤백",
    "### 2.2 UI + Schema 롤백",
    "### 2.3 부분 롤백 (선택적)",
]

REFERENCED_DOCS = [
    "docs/php-ui-architecture.md",
    "docs/php-ui-deployment-checklist.md",
    "docs/php-static-asset-serving.md",
    "docs/php-ui-cache-header-policy.md",
    "docs/php-ui-static-asset-integrity.md",
    "docs/shared-hosting-migration-policy.md",
    "docs/db-web-hosting-constraints.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
]

REFERENCED_SCRIPTS = [
    "scripts/test.sh",
    "scripts/qa.sh",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_php_ui_rollback_checklist_doc_exists():
    """UI rollback 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_ui_rollback_checklist_doc_has_required_sections():
    """사용법, 5단계(전 상태 파악, 범위 결정, 계획 수립, 롤백 실행, 롤백 후 검증,
    모니터링, RCA), 범위 제외, 관련 문서 절이 모두 있다."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_ui_rollback_checklist_doc_has_required_subsections():
    """오류 신호 평가, 배포 변경사항 확인, schema/UI 호환성, UI만 롤백,
    UI+Schema 롤백, 부분 롤백 등의 세부 절이 있다."""
    content = _doc_text()
    for subsection in REQUIRED_SUBSECTIONS:
        assert subsection in content, f"missing required subsection: {subsection}"


def test_php_ui_rollback_checklist_doc_mentions_schema_ui_compatibility():
    """Notes 요구사항 'schema/UI 호환성을 다룬다' 가 실제 본문에 있다."""
    content = _doc_text()
    assert "schema" in content
    assert "UI 호환성" in content or "호환성" in content
    # 추가로 호환성 평가 섹션이 있어야 함
    assert "배포된 UI가 현재 DB schema를 지원하나?" in content
    assert "구 UI가 현재 DB schema를 지원하나?" in content


def test_php_ui_rollback_checklist_doc_covers_three_rollback_strategies():
    """세 가지 롤백 전략(UI만, UI+Schema, 부분)을 모두 다룬다."""
    content = _doc_text()
    assert "UI만 롤백" in content
    assert "UI + Schema 롤백" in content
    assert "부분 롤백" in content


def test_php_ui_rollback_checklist_doc_covers_asset_cache_invalidation():
    """asset 캐시 무효화 절이 있다 — 브라우저 캐시 문제를 다룬다."""
    content = _doc_text()
    assert "asset 캐시 무효화" in content or "Asset 캐시 무효화" in content
    assert "브라우저" in content or "캐시" in content


def test_php_ui_rollback_checklist_doc_covers_pre_rollback_backup():
    """롤백 전에 백업을 받도록 명시한다 — 롤백 실패 시 복구 가능성 확보."""
    content = _doc_text()
    assert "사전 백업" in content or "백업" in content
    assert "tar" in content or "mysqldump" in content


def test_php_ui_rollback_checklist_doc_references_existing_docs():
    """문서가 가리키는 관련 Phase D 문서가 실제로 존재한다(링크 깨짐 없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        # Strip the "docs/" prefix from the path for checking markdown links
        doc_basename = doc.replace("docs/", "")
        assert doc_basename in content, f"missing doc reference: {doc_basename}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_php_ui_rollback_checklist_doc_references_existing_scripts():
    """문서가 가리키는 QA 스크립트가 실제로 존재한다."""
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_php_ui_rollback_checklist_doc_mentions_phase_d():
    """Phase D 체크리스트임을 명시한다."""
    content = _doc_text()
    assert "Phase D" in content
    assert "0521-0610" in content


def test_php_ui_rollback_checklist_doc_emphasizes_schema_ui_decision():
    """schema/UI 호환성 판단이 롤백 범위를 결정하는 핵심임을 강조한다."""
    content = _doc_text()
    # "가장 중요"라는 표현으로 강조
    assert "가장 중요" in content
    # 호환성 판단 결정 트리가 있어야 함
    assert "UI + Schema 함께 변경됨?" in content or "schema와 UI" in content


def test_php_ui_rollback_checklist_doc_mentions_rca_phase():
    """롤백 후 근본 원인 분석(RCA) 절이 있어서, 단순 복구를 넘어
    향후 방지를 다룬다."""
    content = _doc_text()
    assert "RCA" in content or "근본 원인" in content
    assert "테스트 개선" in content
    assert "배포 프로세스 개선" in content


def test_php_ui_rollback_checklist_doc_is_distinct_from_deployment_checklist():
    """배포 체크리스트와 별개의 문서임이 명확하다 — 배포와 롤백은 다른 절차다."""
    content = _doc_text()
    assert "배포 후 오류 발생 시" in content or "오류 발생 시" in content
    # 롤백만의 고유한 내용: pre-rollback assessment, scope decision, RCA
    assert "Pre-Rollback Assessment" in content


def test_php_ui_rollback_checklist_doc_warns_about_schema_rollback_risks():
    """schema 롤백의 위험성(데이터 손실 등)을 경고한다."""
    content = _doc_text()
    assert "⚠️" in content or "경고" in content
    assert "데이터 손실" in content or "손실" in content


def test_php_ui_rollback_checklist_doc_covers_five_rollback_validation_steps():
    """롤백 후 검증이 5개 단계로 구조화되어 있다: 렌더링, asset, 기능, 로그, 헤더."""
    content = _doc_text()
    post_rollback_section = content.split("## 5. 롤백 후 검증")[1].split("\n## ")[0]
    # 각 단계의 제목 확인
    assert "### 5.1 첫 페이지 렌더링" in post_rollback_section
    assert "### 5.2 asset 로드 확인" in post_rollback_section
    assert "### 5.3 주요 기능 테스트" in post_rollback_section
    assert "### 5.4 에러 로그 확인" in post_rollback_section
    assert "### 5.5 캐시 헤더 검증" in post_rollback_section
