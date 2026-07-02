"""`php/composer.json` 이 태스크 0392 의 목표("Composer manifest를 추가한다")와
Notes 요구사항("shared hosting 대응을 위해 의존성은 최소화한다")을 지키는지
확인한다.

`docs/php-namespace-mapping.md` 가 고정한 `MintWiki\\<Module>` namespace 를
psr-4 autoload 로 연결하는지, 그리고 아직 phpunit 등 require-dev 의존성을
들이지 않는지(선택 기준은 0421 에서 문서화)를 검증한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSER_JSON_PATH = REPO_ROOT / "php" / "composer.json"


class TestPhpComposerManifest:
    def test_composer_json_exists(self):
        assert COMPOSER_JSON_PATH.is_file()

    def test_composer_json_is_valid_json(self):
        content = COMPOSER_JSON_PATH.read_text(encoding="utf-8")
        json.loads(content)

    def test_declares_psr4_autoload_for_mintwiki_namespace(self):
        """`docs/php-namespace-mapping.md` 가 고정한 `MintWiki\\` 접두사를
        `src/` 로 매핑한다."""
        manifest = json.loads(COMPOSER_JSON_PATH.read_text(encoding="utf-8"))
        psr4 = manifest.get("autoload", {}).get("psr-4", {})
        assert psr4.get("MintWiki\\") == "src/"

    def test_has_no_runtime_dependencies_beyond_php_itself(self):
        """shared hosting 대응을 위해 require 에는 php 버전 제약만 둔다."""
        manifest = json.loads(COMPOSER_JSON_PATH.read_text(encoding="utf-8"))
        require = manifest.get("require", {})
        assert set(require.keys()) == {"php"}

    def test_has_no_require_dev_dependencies_yet(self):
        """phpunit 선택 기준은 태스크 0421 에서 결정되므로, 이 태스크
        시점에는 require-dev 를 추가하지 않는다."""
        manifest = json.loads(COMPOSER_JSON_PATH.read_text(encoding="utf-8"))
        assert "require-dev" not in manifest

    def test_declares_project_name_and_type(self):
        manifest = json.loads(COMPOSER_JSON_PATH.read_text(encoding="utf-8"))
        assert manifest.get("type") == "project"
        assert isinstance(manifest.get("name"), str) and "/" in manifest["name"]
