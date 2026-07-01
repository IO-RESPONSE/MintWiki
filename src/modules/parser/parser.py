"""평문 텍스트 블록 파서."""
import re
from typing import List, Dict, Any

from modules.parser.model import ParserResult


class PlainTextBlockParser:
    """평문 텍스트 블록을 파싱하는 파서."""

    # HTML 엔티티 패턴: &name; 또는 &#number; 형태
    HTML_ENTITY_PATTERN = re.compile(r'&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);')

    # 제목 패턴: = 텍스트 = (수준 1), == 텍스트 == (수준 2), 등
    # 패턴은 양쪽에 같은 개수의 등호 기호를 요구한다
    HEADING_PATTERN = re.compile(r'^(=+)\s+(.+?)\s+\1$')

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
                # 현재 줄이 제목인지 확인
                heading_match = PlainTextBlockParser.HEADING_PATTERN.match(line)
                if heading_match:
                    # 누적된 문단 블록을 먼저 처리
                    if current_block_lines:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵 (예: [[Category:...]], [[Redirect:...]])
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []

                    # 제목 블록 생성
                    equal_signs = heading_match.group(1)
                    heading_text = heading_match.group(2)
                    heading_level = len(equal_signs)
                    heading_block = {
                        'type': 'heading',
                        'level': heading_level,
                        'content': heading_text,
                    }
                    blocks.append(heading_block)
                else:
                    # 일반 줄은 현재 블록에 추가
                    current_block_lines.append(line)
            else:
                # 빈 줄을 만나면 현재 블록 종료
                if current_block_lines:
                    block_content = '\n'.join(current_block_lines)
                    # 메타데이터 줄은 스킵
                    if not PlainTextBlockParser._is_metadata_line(block_content):
                        block = PlainTextBlockParser._create_block(block_content)
                        blocks.append(block)
                    current_block_lines = []

        # 마지막 블록 처리
        if current_block_lines:
            block_content = '\n'.join(current_block_lines)
            # 메타데이터 줄은 스킵
            if not PlainTextBlockParser._is_metadata_line(block_content):
                block = PlainTextBlockParser._create_block(block_content)
                blocks.append(block)

        return blocks

    @staticmethod
    def _create_block(content: str) -> Dict[str, Any]:
        """
        콘텐츠를 분석하여 적절한 블록을 생성한다.

        Args:
            content: 블록 콘텐츠

        Returns:
            블록 딕셔너리
        """
        # 기본값: 문단 블록
        block = {
            'type': 'paragraph',
            'content': content,
        }
        # 이스케이프된 HTML 검사
        if PlainTextBlockParser._has_escaped_html(content):
            block['has_escaped_html'] = True
        return block

    @staticmethod
    def _is_metadata_line(content: str) -> bool:
        """
        콘텐츠가 메타데이터 줄인지 확인한다.

        메타데이터 줄은 [[Category:...]], [[Redirect:...]] 등의 형식이다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            메타데이터 줄이면 True
        """
        lines = content.split('\n')
        for line in lines:
            # 모든 줄이 메타데이터 형식이어야 함
            if not re.match(r'^\[\[(?:Category|Redirect):', line):
                return False
        return True

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

        제목을 메타데이터로 추출한다.

        Args:
            blocks: 파싱된 블록들

        Returns:
            메타데이터 딕셔너리
        """
        headings = []
        for block in blocks:
            if block.get('type') == 'heading':
                headings.append({
                    'level': block['level'],
                    'text': block['content'],
                })

        return {
            'links': [],
            'categories': [],
            'headings': headings,
        }
