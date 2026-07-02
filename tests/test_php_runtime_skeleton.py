"""`php/` 런타임 기본 디렉터리 골격이 존재하는지 확인한다.

태스크 0391 의 산출물이다 — `docs/php-db-ui-micro-job-prompts-0351-0670.md`
가 정한 대로 `php/src`, `php/public`, `php/tests` 디렉터리만 있으면 되고,
그 안에 실제 PHP 코드가 있을 필요는 없다(후속 Phase B 태스크의 범위).
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHP_ROOT = REPO_ROOT / "php"


class TestPhpRuntimeSkeleton:
    def test_php_root_exists(self):
        assert PHP_ROOT.is_dir()

    def test_src_public_tests_directories_exist(self):
        for name in ["src", "public", "tests"]:
            directory = PHP_ROOT / name
            assert directory.is_dir(), f"missing php/{name}"

    def test_skeleton_directories_are_not_empty_shells(self):
        """빈 디렉터리는 git 이 추적하지 못하므로, 각 디렉터리에 목적을
        설명하는 README 가 있어야 한다."""
        for name in ["src", "public", "tests"]:
            readme = PHP_ROOT / name / "README.md"
            assert readme.is_file(), f"missing php/{name}/README.md"

    def test_src_contains_no_php_files_yet(self):
        """0391 시점 골격 원칙은 `src/`에는 여전히 유효하다 — 실제
        애플리케이션 PHP 소스는 아직 없다. `tests/`는 0393부터,
        `public/`은 0394부터 각각 골격 PHP 파일을 담으므로 이 제약에서
        제외한다."""
        php_files = list((PHP_ROOT / "src").rglob("*.php"))
        assert php_files == [], "unexpected .php files under php/src"
