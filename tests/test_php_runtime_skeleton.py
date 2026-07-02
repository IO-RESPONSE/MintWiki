"""`php/` 런타임 기본 디렉터리 골격이 존재하는지 확인한다.

태스크 0391 의 산출물이다 — `docs/php-db-ui-micro-job-prompts-0351-0670.md`
가 정한 대로 `php/src`, `php/public`, `php/tests` 디렉터리만 있으면 되고,
그 안에 실제 PHP 코드가 있을 필요는 없다(후속 Phase B 태스크의 범위).
`php/src` 는 태스크 0395부터 `Http` value object 등 실제 골격 PHP 파일을
담기 시작하므로, "PHP 파일이 없어야 한다"는 제약은 더 이상 유효하지 않다.
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

    def test_src_http_contains_response_value_object(self):
        """0395부터 `src/Http`에 Response value object가 들어온다."""
        response_file = PHP_ROOT / "src" / "Http" / "Response.php"
        assert response_file.is_file(), "missing php/src/Http/Response.php"

    def test_src_http_contains_request_value_object(self):
        """0396부터 `src/Http`에 Request value object가 들어온다."""
        request_file = PHP_ROOT / "src" / "Http" / "Request.php"
        assert request_file.is_file(), "missing php/src/Http/Request.php"

    def test_src_http_contains_router_skeleton(self):
        """0397부터 `src/Http`에 정적 route 매칭만 지원하는 Router가 들어온다."""
        router_file = PHP_ROOT / "src" / "Http" / "Router.php"
        assert router_file.is_file(), "missing php/src/Http/Router.php"
