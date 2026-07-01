"""평문 텍스트 블록 파서."""
import re
from typing import List, Dict, Any

from modules.parser.model import ParserResult


class PlainTextBlockParser:
    """평문 텍스트 블록을 파싱하는 파서."""

    # HTML 엔티티 패턴: &name; 또는 &#number; 형태
    HTML_ENTITY_PATTERN = re.compile(r'&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);')

    @staticmethod
    def parse(source: str) -> ParserResult:
        """
        평문 텍스트 블록을 파싱한다.

        소스 텍스트를 평문 텍스트 블록들로 분리하여 파싱한다.
        빈 줄은 블록 경계로 간주된다.

        Args:
            source: 파싱할 소스 텍스트

        Returns:
            파싱 결과 (ParserResult 객체)
        """
        blocks = PlainTextBlockParser._parse_blocks(source)
        metadata = PlainTextBlockParser._extract_metadata(blocks)

        return ParserResult(blocks=blocks, metadata=metadata)

    @staticmethod
    def _parse_blocks(source: str) -> List[Dict[str, Any]]:
        """
        소스 텍스트를 블록 단위로 분할하여 파싱한다.

        Args:
            source: 파싱할 소스 텍스트

        Returns:
            파싱된 블록들의 리스트
        """
        if not source or not source.strip():
            return []

        lines = source.split('\n')
        blocks = []
        current_block_lines = []

        for line in lines:
            if line.strip():
                # 비어있지 않은 줄은 현재 블록에 추가
                current_block_lines.append(line)
            else:
                # 빈 줄을 만나면 현재 블록 종료
                if current_block_lines:
                    block_content = '\n'.join(current_block_lines)
                    block = {
                        'type': 'paragraph',
                        'content': block_content,
                    }
                    # 이스케이프된 HTML 검사
                    if PlainTextBlockParser._has_escaped_html(block_content):
                        block['has_escaped_html'] = True
                    blocks.append(block)
                    current_block_lines = []

        # 마지막 블록 처리
        if current_block_lines:
            block_content = '\n'.join(current_block_lines)
            block = {
                'type': 'paragraph',
                'content': block_content,
            }
            # 이스케이프된 HTML 검사
            if PlainTextBlockParser._has_escaped_html(block_content):
                block['has_escaped_html'] = True
            blocks.append(block)

        return blocks

    @staticmethod
    def _has_escaped_html(content: str) -> bool:
        """
        콘텐츠에 이스케이프된 HTML 엔티티가 있는지 확인한다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            이스케이프된 HTML 엔티티가 있으면 True
        """
        return bool(PlainTextBlockParser.HTML_ENTITY_PATTERN.search(content))

    @staticmethod
    def _extract_metadata(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        블록들에서 메타데이터를 추출한다.

        현재는 평문 텍스트 블록만 처리하므로
        기본 메타데이터만 반환한다.

        Args:
            blocks: 파싱된 블록들

        Returns:
            메타데이터 딕셔너리
        """
        return {
            'links': [],
            'categories': [],
            'headings': [],
        }
