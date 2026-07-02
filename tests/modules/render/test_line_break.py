"""줄 바꿈 렌더러 테스트."""
import pytest
from modules.render import render_line_break


class TestRenderLineBreakBasic:
    """줄 바꿈 렌더링 기본 테스트."""

    def test_renders_line_break(self):
        """줄 바꿈을 렌더링한다."""
        result = render_line_break()
        assert result == "<br />"

    def test_renders_consistent_output(self):
        """줄 바꿈이 일관되게 렌더링된다."""
        result1 = render_line_break()
        result2 = render_line_break()
        assert result1 == result2

    def test_renders_self_closing_tag(self):
        """자체 종료 태그로 렌더링한다."""
        result = render_line_break()
        assert result.startswith("<br")
        assert result.endswith("/>")


class TestRenderLineBreakFormat:
    """줄 바꿈 형식 테스트."""

    def test_renders_with_space_before_slash(self):
        """슬래시 앞에 공백이 있다."""
        result = render_line_break()
        assert " /" in result

    def test_renders_without_attributes(self):
        """속성이 없이 렌더링한다."""
        result = render_line_break()
        # <br />만 있어야 하고, class, id, style 같은 속성이 없어야 함
        assert "class" not in result
        assert "id" not in result
        assert "style" not in result
