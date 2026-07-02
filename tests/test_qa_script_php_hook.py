"""`scripts/qa.sh` 가 PHP QA(`php/scripts/qa.sh`)를 선택 실행하는지 확인한다.

태스크 0431 산출물이다. 0430이 만든 `php/scripts/qa.sh`는 그대로 두고,
루트 QA가 `php` CLI 존재 여부에 따라 그것을 실행하거나 명확히 skip하는지만
검증한다. 실제 `scripts/qa.sh`를 그대로 실행하면 내부의 `scripts/test.sh`가
pytest를 재귀 호출하게 되므로, 여기서는 나머지 단계를 스텁으로 대체한
격리된 복사본에서 PHP 훅 동작만 검증한다.
"""
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"

_PYTHON_STUB = "import sys\nsys.exit(0)\n"
_BASH_STUB = "#!/usr/bin/env bash\nexit 0\n"


def _make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _build_isolated_qa_tree(tmp_path: Path, php_qa_body: str) -> Path:
    # qa.sh 마지막 단계인 `git diff --check`가 실패하지 않도록 격리된
    # 트리도 (빈) git 저장소로 만든다.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "qa.sh").write_text(
        QA_SCRIPT_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (scripts_dir / "qa.sh").chmod(0o755)

    (scripts_dir / "check_boundaries.py").write_text(_PYTHON_STUB, encoding="utf-8")
    (scripts_dir / "check_no_app_import_in_modules.py").write_text(
        _PYTHON_STUB, encoding="utf-8"
    )
    (scripts_dir / "check_module_manifests.py").write_text(
        _PYTHON_STUB, encoding="utf-8"
    )
    _make_executable(scripts_dir / "test.sh", _BASH_STUB)

    php_scripts_dir = tmp_path / "php" / "scripts"
    php_scripts_dir.mkdir(parents=True)
    _make_executable(php_scripts_dir / "qa.sh", php_qa_body)

    return tmp_path


def test_qa_sh_references_php_qa_script():
    contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "php/scripts/qa.sh" in contents


def test_qa_sh_guards_php_qa_with_php_cli_check():
    """php CLI 존재 여부를 확인한 뒤에만 PHP QA를 호출해야 한다."""
    contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "command -v php" in contents


def test_qa_sh_runs_php_qa_after_test_sh():
    contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    test_sh_index = contents.index("scripts/test.sh")
    php_qa_index = contents.index("php/scripts/qa.sh")
    assert test_sh_index < php_qa_index


def test_qa_sh_runs_php_qa_when_php_cli_available(tmp_path):
    marker = tmp_path / "php-qa-invoked"
    _build_isolated_qa_tree(
        tmp_path, f"#!/usr/bin/env bash\ntouch '{marker}'\n"
    )

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _make_executable(fake_bin / "php", "#!/usr/bin/env bash\nexit 0\n")

    env = dict(os.environ, PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        ["scripts/qa.sh"], cwd=tmp_path, env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()


def test_qa_sh_skips_php_qa_clearly_when_php_cli_missing(tmp_path):
    """php를 뺀, qa.sh 실행에 꼭 필요한 도구만 있는 PATH를 구성해 검증한다.

    단순히 실제 PATH의 디렉터리를 통째로 제외하면 같은 디렉터리에 있는
    bash/git 같은 필수 도구까지 사라지므로, 필요한 실행 파일만 심볼릭
    링크로 모은 전용 PATH를 만든다.
    """
    import shutil

    marker = tmp_path / "php-qa-invoked"
    _build_isolated_qa_tree(
        tmp_path, f"#!/usr/bin/env bash\ntouch '{marker}'\nexit 1\n"
    )

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    for tool in ("env", "bash", "dirname", "git", "python3"):
        real_path = shutil.which(tool)
        assert real_path is not None, f"테스트 환경에 {tool}이 있어야 한다"
        (fake_bin / tool).symlink_to(real_path)

    env = dict(os.environ, PATH=str(fake_bin))

    result = subprocess.run(
        ["scripts/qa.sh"], cwd=tmp_path, env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists(), "php CLI가 없는데도 PHP QA가 호출되었다"
    assert "php" in (result.stdout + result.stderr).lower()
