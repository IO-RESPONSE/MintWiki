"""PHP 배포 패키지 manifest를 검증한다."""

import fnmatch
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "php" / "deployment-package-manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_php_deployment_package_manifest_exists():
    """0640 배포 패키지 manifest 파일이 php/ 아래에 존재한다."""
    assert MANIFEST_PATH.is_file()


def test_php_deployment_package_manifest_is_valid_json():
    """manifest는 후속 패키징 스크립트가 바로 읽을 수 있는 JSON이다."""
    _manifest()


def test_php_deployment_package_manifest_declares_package_identity():
    """패키지 이름과 package manifest schema version을 명시한다."""
    manifest = _manifest()

    assert manifest["schema_version"] == 1
    assert manifest["package_name"] == "wiki-engine-blueprint-php"
    assert manifest["base_path"] == ".."
    assert "app_version" not in manifest


def test_php_deployment_package_manifest_includes_runtime_inputs():
    """배포에 필요한 PHP 런타임, 설정 샘플, DB schema 입력을 포함한다."""
    manifest = _manifest()

    assert "php/VERSION" in manifest["include"]
    assert "php/composer.json" in manifest["include"]
    assert "php/config/*.sample" in manifest["include"]
    assert "php/public/**" in manifest["include"]
    assert "php/src/**" in manifest["include"]
    assert "db/schema/**" in manifest["include"]


def test_php_deployment_package_manifest_excludes_non_deploy_inputs():
    """문서, 테스트, 태스크 큐, 개발 도구, 기본 vendor 산출물을 제외한다."""
    manifest = _manifest()

    for pattern in [
        ".git/**",
        "docs/**",
        "tasks/**",
        "tests/**",
        "php/tests/**",
        "scripts/**",
        "ops/**",
        "php/vendor/**",
        "php/composer.lock",
    ]:
        assert pattern in manifest["exclude"], f"missing exclude pattern: {pattern}"


def test_php_deployment_package_manifest_declares_vendor_option():
    """Composer 없는 호스팅을 위한 vendor 포함 모드 입력을 분리해 둔다."""
    optional_include = _manifest()["optional_include"]

    assert optional_include["with_vendor"] == [
        "php/composer.lock",
        "php/vendor/**",
    ]
    assert optional_include["without_vendor"] == []


def test_php_deployment_package_manifest_covers_skin_assets():
    """0695: Phase H 스킨(0689-0694)의 공개 CSS 자산과 갱신된 src/Ui/**가
    배포 패키지 include 패턴(php/public/**, php/src/**)에 실제로 걸리는지
    확인한다 — glob 패턴이 바뀌어 스킨 파일이 조용히 빠지는 회귀를 막는다."""
    manifest = _manifest()
    include_patterns = manifest["include"]

    css_dir = REPO_ROOT / "php" / "public" / "assets" / "css"
    css_files = sorted(css_dir.glob("*.css"))
    assert len(css_files) > 0, "스킨 CSS 파일이 존재해야 한다."

    ui_dir = REPO_ROOT / "php" / "src" / "Ui"
    ui_files = sorted(ui_dir.glob("*.php"))
    assert len(ui_files) > 0, "src/Ui 컴포넌트 파일이 존재해야 한다."

    for css_file in css_files:
        relative_path = css_file.relative_to(REPO_ROOT).as_posix()
        assert any(
            fnmatch.fnmatch(relative_path, pattern) for pattern in include_patterns
        ), f"manifest include 패턴이 스킨 CSS 파일을 포함하지 않는다: {relative_path}"

    for ui_file in ui_files:
        relative_path = ui_file.relative_to(REPO_ROOT).as_posix()
        assert any(
            fnmatch.fnmatch(relative_path, pattern) for pattern in include_patterns
        ), f"manifest include 패턴이 src/Ui 파일을 포함하지 않는다: {relative_path}"


def test_php_deployment_package_manifest_covers_phase_j_assets():
    """0713: Phase J(NamuMark 렌더 + 편집 UX + history/discussion, 0704-0712)의
    공개 CSS/JS 자산과 새 도메인 모듈(Modules/Parser, Modules/Render,
    Modules/Discussion, Modules/Revision)이 배포 패키지 include 패턴
    (php/public/**, php/src/**)에 실제로 걸리는지 확인한다 — 0695가 CSS/
    src/Ui만 확인하고 JS 자산과 Modules/ 하위 디렉터리는 다루지 않아 새
    js 파일이나 모듈이 조용히 빠지는 회귀를 막는다."""
    manifest = _manifest()
    include_patterns = manifest["include"]

    js_dir = REPO_ROOT / "php" / "public" / "assets" / "js"
    js_files = sorted(js_dir.glob("*.js"))
    assert len(js_files) > 0, "편집 UX(툴바/미리보기) JS 파일이 존재해야 한다."

    phase_j_module_dirs = [
        REPO_ROOT / "php" / "src" / "Modules" / "Parser",
        REPO_ROOT / "php" / "src" / "Modules" / "Render",
        REPO_ROOT / "php" / "src" / "Modules" / "Discussion",
        REPO_ROOT / "php" / "src" / "Modules" / "Revision",
    ]
    module_files = []
    for module_dir in phase_j_module_dirs:
        found = sorted(module_dir.glob("*.php"))
        assert len(found) > 0, f"{module_dir}에 PHP 파일이 존재해야 한다."
        module_files.extend(found)

    for js_file in js_files:
        relative_path = js_file.relative_to(REPO_ROOT).as_posix()
        assert any(
            fnmatch.fnmatch(relative_path, pattern) for pattern in include_patterns
        ), f"manifest include 패턴이 Phase J JS 자산을 포함하지 않는다: {relative_path}"

    for module_file in module_files:
        relative_path = module_file.relative_to(REPO_ROOT).as_posix()
        assert any(
            fnmatch.fnmatch(relative_path, pattern) for pattern in include_patterns
        ), f"manifest include 패턴이 Phase J 도메인 모듈을 포함하지 않는다: {relative_path}"


def test_php_deployment_package_manifest_patterns_are_reviewable():
    """패턴은 상대 경로이며 중복과 상위 디렉터리 탈출을 허용하지 않는다."""
    manifest = _manifest()
    pattern_groups = [
        manifest["include"],
        manifest["exclude"],
        manifest["optional_include"]["with_vendor"],
        manifest["optional_include"]["without_vendor"],
    ]

    for patterns in pattern_groups:
        assert len(patterns) == len(set(patterns))
        for pattern in patterns:
            assert not pattern.startswith("/")
            assert ".." not in Path(pattern).parts
