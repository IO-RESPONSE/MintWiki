"""렌더/캐시 MVP 단계 통합 QA 체크리스트.

각 테스트 클래스는 src/modules/render/README.md 와 src/modules/cache/README.md 에
문서화된 규칙 하나에 대응한다. 개별 유닛 테스트가 이미 각 렌더러/새니타이저를
검증하므로, 여기서는 안전한 HTML 렌더링 -> 메타데이터 추출 -> 렌더 캐시 저장/조회로
이어지는 전체 흐름이 함께 동작할 때도 각 규칙이 그대로 유지되는지 확인한다.
"""
import pytest

from modules.cache import Cache, InMemoryCacheBackend, build_render_cache_key
from modules.render.categories_metadata import render_categories_metadata
from modules.render.css_sanitizer import sanitize_css_value
from modules.render.external_link import render_external_link
from modules.render.footnotes_section import render_footnotes_section
from modules.render.heading import render_heading
from modules.render.model import RenderResult
from modules.render.paragraph import render_plain_paragraph
from modules.render.simple_table import render_simple_table


class TestHtmlEscapingChecklist:
    """규칙 1: 사용자 제공 텍스트는 캐시를 거쳐도 이스케이프된 상태를 유지해야 한다."""

    @pytest.mark.asyncio
    async def test_script_injection_survives_cache_round_trip_escaped(self):
        """스크립트 삽입 시도가 렌더링과 캐시 조회 이후에도 이스케이프된 채로 남는다."""
        malicious = "<script>alert('xss')</script>"
        html = render_plain_paragraph(malicious)
        assert "<script>" not in html

        backend = InMemoryCacheBackend()
        cache = Cache(backend)
        result = RenderResult(html=html, metadata={})
        await cache.set_render_result(malicious, result)

        cached = await cache.get_render_result(malicious)
        assert cached is not None
        assert "<script>" not in cached.html
        assert cached.html == html

    @pytest.mark.asyncio
    async def test_heading_and_footnote_escaping_preserved_after_cache_hit(self):
        """제목과 각주의 이스케이프 결과가 캐시 히트 후에도 동일하다."""
        heading_html = render_heading(1, "<b>제목</b>")
        footnotes_html = render_footnotes_section(["<img onerror=alert(1)>"])
        combined_html = heading_html + footnotes_html

        backend = InMemoryCacheBackend()
        cache = Cache(backend)
        source = "제목 + 각주 문서"
        await cache.set_render_result(source, RenderResult(html=combined_html, metadata={}))

        cached = await cache.get_render_result(source)
        assert cached is not None
        assert "&lt;b&gt;" in cached.html
        assert "&lt;img" in cached.html
        assert "<img onerror" not in cached.html


class TestCssSanitizationChecklist:
    """규칙 2: 테이블 셀 style 속성은 위험한 CSS 값을 항상 걸러내야 한다."""

    def test_table_cell_rejects_dangerous_style_but_renders_content(self):
        """위험한 style 값은 속성에서 제거되고 셀 내용은 정상적으로 렌더링된다."""
        table = {
            "rows": [
                {
                    "type": "data",
                    "cells": [
                        {"content": "안전한 셀", "style": "expression(alert(1))"},
                    ],
                }
            ]
        }
        html = render_simple_table(table)
        assert "expression" not in html
        assert "<td>안전한 셀</td>" in html

    def test_table_cell_keeps_safe_style_value(self):
        """안전한 style 값은 그대로 유지된다."""
        table = {
            "rows": [
                {"type": "data", "cells": [{"content": "셀", "style": "color: red;"}]}
            ]
        }
        html = render_simple_table(table)
        assert 'style="color: red;"' in html

    @pytest.mark.parametrize(
        "dangerous_value",
        [
            "expression(alert(1))",
            "url(javascript:alert(1))",
            "@import url(evil.css)",
            "\\0 color",
        ],
    )
    def test_sanitizer_rejects_all_known_dangerous_css_values(self, dangerous_value):
        """README에 나열된 위험 CSS 패턴이 모두 거부되는지 확인한다."""
        assert sanitize_css_value(dangerous_value) is None


class TestUrlSanitizationChecklist:
    """규칙 3: 외부 링크 렌더링은 안전하지 않은 URL 스킴을 실행 가능한 형태로 남기지 않는다."""

    @pytest.mark.parametrize(
        "unsafe_url",
        [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
        ],
    )
    def test_external_link_neutralizes_unsafe_schemes(self, unsafe_url):
        """안전하지 않은 스킴은 href에 그대로 삽입되지만 이스케이프되어 실행되지 않는다."""
        html = render_external_link(unsafe_url, "링크")
        assert "<script>" not in html
        assert html.startswith('<a href="')
        assert 'rel="noopener noreferrer"' in html

    def test_external_link_preserves_safe_scheme_and_relative_paths(self):
        """안전한 스킴과 상대 경로는 href에 그대로 사용된다."""
        assert 'href="https://example.com"' in render_external_link("https://example.com")
        assert 'href="/wiki/Home"' in render_external_link("/wiki/Home")


class TestMetadataExtractionChecklist:
    """렌더링 중 추출된 헤딩/링크/카테고리/각주 메타데이터가 캐시를 거쳐도 보존된다."""

    @pytest.mark.asyncio
    async def test_categories_metadata_and_render_metadata_round_trip_via_cache(self):
        """카테고리 렌더링 결과와 구조화된 메타데이터가 캐시 조회 후에도 일치한다."""
        categories_html = render_categories_metadata(["역사", "과학<script>"])
        assert "&lt;script&gt;" in categories_html

        metadata = {
            "headings": [{"level": 1, "text": "제목", "id": "제목"}],
            "links": ["https://example.com"],
            "categories": ["역사", "과학<script>"],
            "footnotes": [{"id": "fn-1", "text": "각주"}],
        }
        result = RenderResult(html=categories_html, metadata=metadata)

        backend = InMemoryCacheBackend()
        cache = Cache(backend)
        source = "카테고리 문서"
        await cache.set_render_result(source, result)

        cached = await cache.get_render_result(source)
        assert cached is not None
        assert cached.metadata["categories"] == metadata["categories"]
        assert cached.metadata["headings"] == metadata["headings"]
        assert cached.metadata["footnotes"] == metadata["footnotes"]
        assert "&lt;script&gt;" in cached.html


class TestRenderCacheKeyChecklist:
    """규칙 5: 캐시 키는 결정적이며 파서 버전에 따라 캐시를 분리해야 한다."""

    def test_same_source_and_version_produce_same_key(self):
        """동일한 소스와 파서 버전은 항상 동일한 캐시 키를 만든다."""
        key_a = build_render_cache_key("동일 문서", "1.0.0")
        key_b = build_render_cache_key("동일 문서", "1.0.0")
        assert key_a == key_b
        assert key_a.startswith("render:v1.0.0:")

    def test_parser_version_bump_changes_key_and_misses_old_cache(self):
        """파서 버전이 바뀌면 캐시 키가 달라지고 이전 캐시는 미스로 처리된다."""
        assert build_render_cache_key("동일 문서", "1.0.0") != build_render_cache_key(
            "동일 문서", "2.0.0"
        )

    @pytest.mark.asyncio
    async def test_cache_lookup_misses_across_parser_versions(self):
        """구버전 파서로 저장한 캐시는 신버전 파서 조회에서 히트하지 않는다."""
        backend = InMemoryCacheBackend()
        source = "버전 분리 문서"

        cache_v1 = Cache(backend, parser_version="1.0.0")
        cache_v2 = Cache(backend, parser_version="2.0.0")

        await cache_v1.set_render_result(source, RenderResult(html="<p>v1</p>", metadata={}))

        assert await cache_v2.get_render_result(source) is None
        cached_v1 = await cache_v1.get_render_result(source)
        assert cached_v1 is not None
        assert cached_v1.html == "<p>v1</p>"
