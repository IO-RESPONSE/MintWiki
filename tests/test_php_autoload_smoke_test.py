"""`php/tests/AutoloadSmokeTest.php` 가 태스크 0393 의 목표
("PHP autoload smoke test를 추가한다")와 Notes 요구사항("네트워크 의존
없이 동작하게 한다")을 지키는지 확인한다.

`composer.json` 이 선언한 `MintWiki\\` PSR-4 매핑이 `composer install`이
생성한 오토로더에 실제로 등록되는지를, `composer`와 `php` CLI만으로
검증한다. `composer.json`은 `php` 엔진 제약 외에 패키지를 선언하지 않으므로
(`tests/test_php_composer_manifest.py`), `composer install`은 네트워크
접근 없이 끝난다 — 이를 `COMPOSER_DISABLE_NETWORK=1`로 강제한다.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHP_ROOT = REPO_ROOT / "php"
SMOKE_TEST_PATH = PHP_ROOT / "tests" / "AutoloadSmokeTest.php"


def _composer_install():
    env = dict(os.environ, COMPOSER_DISABLE_NETWORK="1")
    return subprocess.run(
        ["composer", "install", "--no-interaction", "--no-progress"],
        cwd=PHP_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class TestPhpAutoloadSmokeTest:
    def test_smoke_test_file_exists(self):
        assert SMOKE_TEST_PATH.is_file()

    def test_smoke_test_has_valid_php_syntax(self):
        result = subprocess.run(
            ["php", "-l", str(SMOKE_TEST_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_smoke_test_passes_after_offline_composer_install(self):
        install = _composer_install()
        assert install.returncode == 0, install.stdout + install.stderr

        result = subprocess.run(
            ["php", str(SMOKE_TEST_PATH)],
            cwd=PHP_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_smoke_test_fails_clearly_when_vendor_missing(self, tmp_path):
        """vendor/ 없이 실행하면 크래시 대신 명확한 안내 메시지로
        exit code 1 을 반환해야 한다."""
        isolated_tests_dir = tmp_path / "tests"
        isolated_tests_dir.mkdir()
        script_copy = isolated_tests_dir / "AutoloadSmokeTest.php"
        script_copy.write_text(
            SMOKE_TEST_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )

        result = subprocess.run(
            ["php", str(script_copy)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "composer install" in (result.stdout + result.stderr)
