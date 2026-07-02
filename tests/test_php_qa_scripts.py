"""`php/scripts/test.sh` 와 `php/scripts/qa.sh` 가 태스크 0430 의
목표("PHP QA 스크립트 골격을 추가한다")와 Notes 요구사항("test/static
check 명령을 한 곳에 둔다")을 지키는지 확인한다.

`docs/php-test-bootstrap.md` 가 예고한 대로, `test.sh`가 `php/tests/`
아래 모든 `*Test.php`를 순회 실행하는 통합 러너이고 `qa.sh`가 그 실행을
포함한 단일 QA 진입점인지를, 실제로 스크립트를 실행해 검증한다.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHP_ROOT = REPO_ROOT / "php"
SCRIPTS_DIR = PHP_ROOT / "scripts"
TEST_SH_PATH = SCRIPTS_DIR / "test.sh"
QA_SH_PATH = SCRIPTS_DIR / "qa.sh"


def _composer_install():
    env = dict(os.environ, COMPOSER_DISABLE_NETWORK="1")
    return subprocess.run(
        ["composer", "install", "--no-interaction", "--no-progress"],
        cwd=PHP_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class TestPhpQaScripts:
    def test_test_sh_exists_and_is_executable(self):
        assert TEST_SH_PATH.is_file()
        assert os.access(TEST_SH_PATH, os.X_OK)

    def test_qa_sh_exists_and_is_executable(self):
        assert QA_SH_PATH.is_file()
        assert os.access(QA_SH_PATH, os.X_OK)

    def test_test_sh_has_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(TEST_SH_PATH)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_qa_sh_has_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(QA_SH_PATH)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_qa_sh_invokes_test_sh(self):
        """"test/static check 명령을 한 곳에 둔다"는 Notes 요구사항: qa.sh
        가 test.sh 실행을 포함한다."""
        content = QA_SH_PATH.read_text(encoding="utf-8")
        assert "scripts/test.sh" in content

    def test_test_sh_runs_every_test_file_and_passes(self):
        install = _composer_install()
        assert install.returncode == 0, install.stdout + install.stderr

        result = subprocess.run(
            ["./scripts/test.sh"], cwd=PHP_ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

        expected_files = sorted(PHP_ROOT.glob("tests/**/*Test.php"))
        assert len(expected_files) > 0
        for test_file in expected_files:
            relative_path = test_file.relative_to(PHP_ROOT).as_posix()
            assert f"PASS {relative_path}" in result.stdout

        assert f"{len(expected_files)}/{len(expected_files)} passed" in result.stdout

    def test_test_sh_runs_from_repository_root_too(self):
        """스크립트가 자기 위치 기준으로 php/ 로 이동하므로, 저장소
        루트에서 호출해도 동일하게 동작한다."""
        install = _composer_install()
        assert install.returncode == 0, install.stdout + install.stderr

        result = subprocess.run(
            [str(TEST_SH_PATH)], cwd=REPO_ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_qa_sh_runs_successfully(self):
        install = _composer_install()
        assert install.returncode == 0, install.stdout + install.stderr

        result = subprocess.run(
            ["./scripts/qa.sh"], cwd=PHP_ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_test_sh_fails_clearly_when_a_test_file_fails(self):
        install = _composer_install()
        assert install.returncode == 0, install.stdout + install.stderr

        broken_dir = PHP_ROOT / "tests" / "Tmp0430QaScriptCheck"
        broken_file = broken_dir / "BrokenTest.php"
        broken_dir.mkdir()
        try:
            broken_file.write_text(
                "<?php\n"
                "declare(strict_types=1);\n"
                'fwrite(STDERR, "intentional failure for 0430 qa script test\\n");\n'
                "exit(1);\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["./scripts/test.sh"], cwd=PHP_ROOT, capture_output=True, text=True
            )
            assert result.returncode == 1
            assert "FAIL tests/Tmp0430QaScriptCheck/BrokenTest.php" in result.stdout
            assert "intentional failure for 0430 qa script test" in (
                result.stdout + result.stderr
            )
        finally:
            broken_file.unlink()
            broken_dir.rmdir()

    def test_test_sh_fails_clearly_when_vendor_missing(self, tmp_path):
        """`vendor/autoload.php`가 없으면 크래시 대신 명확한 안내 메시지로
        exit code 1 을 반환해야 한다(docs/php-test-bootstrap.md의
        AutoloadSmokeTest와 같은 원칙)."""
        isolated_scripts_dir = tmp_path / "scripts"
        isolated_scripts_dir.mkdir()
        script_copy = isolated_scripts_dir / "test.sh"
        script_copy.write_text(
            TEST_SH_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        script_copy.chmod(0o755)
        (tmp_path / "tests").mkdir()

        result = subprocess.run(
            [str(script_copy)], capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "composer install" in (result.stdout + result.stderr)
