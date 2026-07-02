"""렌더 픽스처 러너 테스트."""
import pytest
from tests.modules.render.fixture_runner import FixtureRunner
from modules.render import (
    render_plain_paragraph,
    render_bold,
    render_italic,
    render_strike,
    render_heading,
    render_external_link,
    render_internal_link,
    render_line_break,
    render_code_block,
)


class TestFixtureRunnerLoading:
    """픽스처 러너의 로딩 기능 테스트."""

    def test_initializes_with_default_fixture_dir(self):
        """기본 픽스처 디렉토리로 초기화된다."""
        runner = FixtureRunner()
        assert runner.fixture_dir.exists()
        assert runner.fixture_dir.name == "fixtures"

    def test_initializes_with_custom_fixture_dir(self, tmp_path):
        """커스텀 픽스처 디렉토리로 초기화될 수 있다."""
        runner = FixtureRunner(fixture_dir=str(tmp_path))
        assert runner.fixture_dir == tmp_path

    def test_loads_fixture_file(self):
        """픽스처 파일을 로드한다."""
        runner = FixtureRunner()
        content = runner.load_fixture("simple_paragraph.html")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_raises_error_for_missing_fixture(self):
        """존재하지 않는 픽스처 파일에 대해 에러를 발생시킨다."""
        runner = FixtureRunner()
        with pytest.raises(FileNotFoundError):
            runner.load_fixture("nonexistent_fixture.html")

    def test_lists_all_fixtures(self):
        """모든 픽스처 파일을 나열한다."""
        runner = FixtureRunner()
        fixtures = runner.list_fixtures()
        assert isinstance(fixtures, list)
        assert len(fixtures) > 0
        assert all(f.endswith(".html") for f in fixtures)
        # 정렬된 상태인지 확인
        assert fixtures == sorted(fixtures)

    def test_fixture_list_is_alphabetically_ordered(self):
        """픽스처 목록이 알파벳 순서로 정렬된다."""
        runner = FixtureRunner()
        fixtures = runner.list_fixtures()
        assert fixtures == sorted(fixtures)


class TestFixtureRunnerExecution:
    """픽스처 러너의 실행 기능 테스트."""

    def test_runs_fixture_with_simple_paragraph(self):
        """simple_paragraph 픽스처에 대해 렌더 함수를 실행한다."""
        runner = FixtureRunner()
        result = runner.run_fixture(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Hello, World!",
        )
        assert result is True

    def test_detects_fixture_mismatch(self):
        """픽스처 불일치를 감지한다."""
        runner = FixtureRunner()
        result = runner.run_fixture(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Wrong content",
        )
        assert result is False

    def test_run_fixture_returns_boolean(self):
        """픽스처 실행 결과는 부울값을 반환한다."""
        runner = FixtureRunner()
        result = runner.run_fixture(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Hello, World!",
        )
        assert isinstance(result, bool)

    def test_run_fixture_with_external_link(self):
        """external_link 픽스처에 대해 렌더 함수를 실행한다."""
        runner = FixtureRunner()
        result = runner.run_fixture(
            "external_link.html",
            render_external_link,
            "https://example.com",
        )
        assert result is True

    def test_run_fixture_handles_missing_file_gracefully(self):
        """존재하지 않는 픽스처 파일은 에러를 발생시킨다."""
        runner = FixtureRunner()
        with pytest.raises(FileNotFoundError):
            runner.run_fixture(
                "nonexistent_fixture.html",
                render_plain_paragraph,
                "test",
            )


class TestFixtureRunnerComparison:
    """픽스처 러너의 비교 기능 테스트."""

    def test_returns_comparison_result_on_success(self):
        """성공 시 비교 결과를 반환한다."""
        runner = FixtureRunner()
        result = runner.run_fixture_with_comparison(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Hello, World!",
        )
        assert result["success"] is True
        assert "expected" in result
        assert "actual" in result
        assert "fixture_file" in result
        assert "mismatch" not in result

    def test_returns_detailed_mismatch_info(self):
        """불일치 시 상세 정보를 반환한다."""
        runner = FixtureRunner()
        result = runner.run_fixture_with_comparison(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Wrong content",
        )
        assert result["success"] is False
        assert "expected" in result
        assert "actual" in result
        assert "fixture_file" in result
        assert "mismatch" in result
        assert result["fixture_file"] == "simple_paragraph.html"

    def test_comparison_result_contains_required_fields(self):
        """비교 결과에 필수 필드를 포함한다."""
        runner = FixtureRunner()
        result = runner.run_fixture_with_comparison(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Hello, World!",
        )
        assert "success" in result
        assert "expected" in result
        assert "actual" in result
        assert "fixture_file" in result

    def test_comparison_includes_mismatch_on_failure(self):
        """비교 실패 시 mismatch 정보를 포함한다."""
        runner = FixtureRunner()
        result = runner.run_fixture_with_comparison(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Wrong text",
        )
        assert "mismatch" in result
        assert "Expected:" in result["mismatch"]
        assert "Actual:" in result["mismatch"]

    def test_comparison_result_is_dict(self):
        """비교 결과는 딕셔너리이다."""
        runner = FixtureRunner()
        result = runner.run_fixture_with_comparison(
            "simple_paragraph.html",
            render_plain_paragraph,
            "Hello, World!",
        )
        assert isinstance(result, dict)


class TestFixtureRunnerWithKorean:
    """한글 지원 테스트."""

    def test_handles_korean_text_in_fixture(self):
        """한글 텍스트가 있는 픽스처를 처리한다."""
        runner = FixtureRunner()
        content = runner.load_fixture("korean_text.html")
        assert "한글" in content

    def test_lists_korean_fixtures(self):
        """한글 텍스처 파일명을 포함한 목록을 반환한다."""
        runner = FixtureRunner()
        fixtures = runner.list_fixtures()
        assert "korean_text.html" in fixtures
        assert "mixed_language.html" in fixtures
