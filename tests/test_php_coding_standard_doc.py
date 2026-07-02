"""`docs/php-coding-standard.md` 가 태스크 0422 의 목표("PHP 코딩 표준을
문서화한다")와 Notes 요구사항("PSR-4, strict_types, namespace 규칙을
둔다")을 실제로 고정하고 있으며, 문서가 서술하는 규칙이 `php/` 트리의
실제 상태(composer.json 오토로드 설정, 기존 소스 파일의 패턴)와 어긋나지
않는지 확인한다.
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-coding-standard.md"
PHP_README_PATH = REPO_ROOT / "php" / "README.md"
PHP_COMPOSER_PATH = REPO_ROOT / "php" / "composer.json"
PHP_SRC_DIR = REPO_ROOT / "php" / "src"

REQUIRED_DOC_HEADINGS = [
    "## PSR-4 오토로딩 규칙",
    "## strict_types 규칙",
    "## Namespace 규칙",
    "## 클래스 선언 규칙",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]


def test_php_coding_standard_doc_exists():
    """PHP 코딩 표준 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_coding_standard_doc_has_required_sections():
    """PSR-4, strict_types, namespace, 클래스 선언, 범위 제외, 관련 문서
    절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_coding_standard_doc_describes_psr4_and_classmap_exception():
    """태스크 Notes 요구사항: PSR-4 규칙과 `src/Modules/` classmap 예외를
    실제 composer.json 값과 함께 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert 'MintWiki\\' in content
    assert "classmap" in content
    assert "src/Modules/" in content


def test_php_coding_standard_doc_states_strict_types_rule():
    """태스크 Notes 요구사항: strict_types 선언 규칙을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "declare(strict_types=1)" in content


def test_php_coding_standard_doc_references_namespace_mapping_doc():
    """태스크 Notes 요구사항: namespace 규칙은 이 문서가 정본인
    `docs/php-namespace-mapping.md`를 가리켜 중복 정의하지 않는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-namespace-mapping.md" in content


def test_php_coding_standard_doc_defers_out_of_scope_tasks():
    """정적 분석 계획(0423)과 도메인 framework 금지 규칙(0424)은 이
    태스크의 범위가 아님을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "0423" in content
    assert "0424" in content


def test_php_coding_standard_doc_references_related_docs():
    """전략 문서, 테스트 bootstrap 문서, php/ 트리 README와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/php-test-bootstrap.md",
        "php/README.md",
        "php/tests/README.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_readme_links_to_coding_standard_doc():
    """`php/README.md`가 새 코딩 표준 문서를 가리켜, php/ 트리를 보는
    사람이 규칙을 바로 찾을 수 있다."""
    content = PHP_README_PATH.read_text(encoding="utf-8")
    assert "docs/php-coding-standard.md" in content


def test_php_composer_manifest_matches_documented_autoload_rules():
    """문서가 근거로 드는 PSR-4/classmap 설정이 실제 composer.json과
    일치한다."""
    manifest = json.loads(PHP_COMPOSER_PATH.read_text(encoding="utf-8"))
    autoload = manifest["autoload"]
    assert autoload["psr-4"] == {"MintWiki\\": "src/"}
    assert autoload["classmap"] == ["src/Modules/"]


def _iter_php_source_files():
    return sorted(PHP_SRC_DIR.rglob("*.php"))


def test_all_php_src_files_declare_strict_types_first():
    """`php/src/` 아래 모든 파일이 문서가 규정한 순서
    (`<?php` → 빈 줄 → `declare(strict_types=1);`)를 실제로 지킨다."""
    files = _iter_php_source_files()
    assert files, "expected at least one PHP source file under php/src/"
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "<?php", f"{path}: first line must be '<?php'"
        assert lines[1] == "", f"{path}: second line must be blank"
        assert lines[2] == "declare(strict_types=1);", (
            f"{path}: third line must declare strict_types"
        )


def test_all_php_src_files_use_mintwiki_namespace_prefix():
    """`php/src/` 아래 모든 파일이 `MintWiki\\` 최상위 접두사를 쓴다."""
    for path in _iter_php_source_files():
        content = path.read_text(encoding="utf-8")
        match = re.search(r"^namespace (MintWiki(?:\\[A-Za-z0-9_]+)*);", content, re.MULTILINE)
        assert match, f"{path}: missing top-level MintWiki namespace declaration"


def test_php_modules_namespace_omits_modules_segment():
    """`src/Modules/<Module>/` 아래 클래스는 문서가 설명하는 대로
    namespace 에 `Modules` 세그먼트를 포함하지 않는다."""
    modules_dir = PHP_SRC_DIR / "Modules"
    files = sorted(modules_dir.rglob("*.php"))
    assert files, "expected at least one PHP source file under php/src/Modules/"
    for path in files:
        content = path.read_text(encoding="utf-8")
        match = re.search(
            r"^namespace (MintWiki\\(?:Modules\\)?[A-Za-z0-9_]+);",
            content,
            re.MULTILINE,
        )
        assert match, f"{path}: missing namespace declaration"
        assert "\\Modules\\" not in match.group(1), (
            f"{path}: namespace must not include a Modules segment"
        )
