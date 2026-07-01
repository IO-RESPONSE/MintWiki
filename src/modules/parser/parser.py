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

    # 내부 링크 패턴: [[LinkName]] 또는 [[LinkName|Label]]
    INTERNAL_LINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    # 외부 링크 패턴: [URL] 또는 [URL label] 또는 [URL|label]
    EXTERNAL_LINK_PATTERN = re.compile(r'\[([^\s\]|]+)(?:(?:\s+|[|])[^\]]*)?\]')

    # 굵은 텍스트 패턴: '''text'''
    BOLD_PATTERN = re.compile(r"'''([^']+)'''", re.DOTALL)

    # 이탤릭 텍스트 패턴: ''text''
    ITALIC_PATTERN = re.compile(r"''([^']+)''", re.DOTALL)

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
        metadata = PlainTextBlockParser._extract_metadata(source, blocks)

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
    def _extract_metadata(source: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        소스 텍스트와 블록들에서 메타데이터를 추출한다.

        제목, 링크, 카테고리, 리다이렉트, 외부 링크를 메타데이터로 추출한다.

        Args:
            source: 원본 소스 텍스트
            blocks: 파싱된 블록들

        Returns:
            메타데이터 딕셔너리
        """
        headings = []
        links = []
        external_links = []
        categories = []
        redirects = []

        # 소스에서 메타데이터 라인 추출
        lines = source.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('[[Category:') and line.endswith(']]'):
                category_name = line[len('[[Category:'):-2]
                categories.append(category_name)
            elif line.startswith('[[Redirect:') and line.endswith(']]'):
                redirect_target = line[len('[[Redirect:'):-2]
                redirects.append({'from': '', 'to': redirect_target})

        # 블록에서 메타데이터 추출
        for block in blocks:
            if block.get('type') == 'heading':
                headings.append({
                    'level': block['level'],
                    'text': block['content'],
                })
            elif block.get('type') == 'paragraph':
                # 문단에서 내부 링크 추출
                content = block.get('content', '')
                extracted_links, extracted_categories, extracted_redirects = \
                    PlainTextBlockParser._extract_links_from_content(content)
                links.extend(extracted_links)
                categories.extend(extracted_categories)
                redirects.extend(extracted_redirects)
                # 문단에서 외부 링크 추출
                extracted_external_links = PlainTextBlockParser._extract_external_links_from_content(content)
                external_links.extend(extracted_external_links)

        # 중복 제거하되 순서 유지
        links = list(dict.fromkeys(links))
        categories = list(dict.fromkeys(categories))
        external_links = list(dict.fromkeys(external_links))

        metadata = {
            'links': links,
            'categories': categories,
            'headings': headings,
        }

        # external_links가 있으면 추가
        if external_links:
            metadata['external_links'] = external_links

        # redirects가 있으면 추가
        if redirects:
            metadata['redirects'] = redirects

        return metadata

    @staticmethod
    def _extract_links_from_content(content: str) -> tuple:
        """
        콘텐츠에서 내부 링크, 카테고리, 리다이렉트를 추출한다.

        내부 링크 형식:
        - [[LinkName]] - 일반 링크
        - [[Category:Name]] - 카테고리
        - [[Redirect:Name]] - 리다이렉트

        Args:
            content: 파싱할 콘텐츠

        Returns:
            (links, categories, redirects) 튜플
        """
        links = []
        categories = []
        redirects = []

        matches = PlainTextBlockParser.INTERNAL_LINK_PATTERN.findall(content)
        for match in matches:
            if match.startswith('Category:'):
                category_name = match[len('Category:'):]
                categories.append(category_name)
            elif match.startswith('Redirect:'):
                redirect_target = match[len('Redirect:'):]
                redirects.append({'from': '', 'to': redirect_target})
            else:
                # 일반 링크
                links.append(match)

        return links, categories, redirects

    @staticmethod
    def _extract_external_links_from_content(content: str) -> list:
        """
        콘텐츠에서 외부 링크를 추출한다.

        외부 링크 형식:
        - [URL] - URL만 있는 링크
        - [URL label] - URL과 레이블이 있는 링크 (공백으로 구분)
        - [URL|label] - URL과 레이블이 있는 링크 (파이프로 구분)

        Args:
            content: 파싱할 콘텐츠

        Returns:
            외부 링크 목록
        """
        external_links = []

        for match in PlainTextBlockParser.EXTERNAL_LINK_PATTERN.finditer(content):
            url = match.group(1)
            # URL이 유효한 외부 링크 형식인지 확인 (http://, https://, ftp:// 등)
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')):
                external_links.append(url)

        return external_links
