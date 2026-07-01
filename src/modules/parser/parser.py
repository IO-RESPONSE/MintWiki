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

    # 굵은 텍스트 패턴: '''text''' (중첩된 마크 지원)
    BOLD_PATTERN = re.compile(r"'''(.+?)'''", re.DOTALL)

    # 이탤릭 텍스트 패턴: ''text'' (중첩된 마크 지원)
    ITALIC_PATTERN = re.compile(r"''(.+?)''", re.DOTALL)

    # 취소선 텍스트 패턴: ~~text~~ (중첩된 마크 지원)
    STRIKE_PATTERN = re.compile(r"~~(.+?)~~", re.DOTALL)

    # 순서 없는 목록 패턴: * 텍스트 (수준 1), ** 텍스트 (수준 2), 등
    UNORDERED_LIST_PATTERN = re.compile(r'^(\*+)\s+(.+)$')

    # 순서 있는 목록 패턴: # 텍스트 (수준 1), ## 텍스트 (수준 2), 등
    ORDERED_LIST_PATTERN = re.compile(r'^(#+)\s+(.+)$')

    # 수평선 패턴: ---- (4개 이상의 대시)
    HORIZONTAL_RULE_PATTERN = re.compile(r'^-{4,}$')

    # 줄 바꿈 매크로 패턴: \\ (두 개의 백슬래시)
    LINE_BREAK_PATTERN = re.compile(r'^\\\\$')

    # 넓히지않기 블록 시작 패턴: <nowiki>
    NOWIKI_START_PATTERN = re.compile(r'^<nowiki>(.*)', re.IGNORECASE)

    # 넓히지않기 블록 종료 패턴: </nowiki>
    NOWIKI_END_PATTERN = re.compile(r'(.*?)</nowiki>(.*)', re.IGNORECASE)

    # 코드 블록 시작 패턴: {{{
    CODE_START_PATTERN = re.compile(r'^(\{\{\{)(.*)')

    # 코드 블록 종료 패턴: }}}
    CODE_END_PATTERN = re.compile(r'(.*?)\}\}\}(.*)')

    # 테이블 행 패턴: ||cell1||cell2||cell3|| (시작과 끝에 ||)
    TABLE_ROW_PATTERN = re.compile(r'^\|\|(.+)\|\|$')

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
        in_list = False
        in_table = False
        i = 0

        while i < len(lines):
            line = lines[i]

            # 현재 줄이 코드 블록 시작인지 확인
            code_start_match = PlainTextBlockParser.CODE_START_PATTERN.match(line)
            if code_start_match:
                # 누적된 블록을 먼저 처리
                if current_block_lines:
                    block_content = '\n'.join(current_block_lines)
                    if not PlainTextBlockParser._is_metadata_line(block_content):
                        block = PlainTextBlockParser._create_block(block_content)
                        blocks.append(block)
                    current_block_lines = []
                    in_list = False

                # 시작 태그 이후의 콘텐츠
                content_after_start = code_start_match.group(2)

                # 닫는 태그가 같은 줄에 있는지 확인
                end_match = PlainTextBlockParser.CODE_END_PATTERN.match(content_after_start)
                if end_match:
                    # 같은 줄에 {{{content}}} 형식
                    code_content = end_match.group(1)
                    remaining_content = end_match.group(2)

                    # 코드 블록 생성
                    code_block = {
                        'type': 'code',
                        'content': code_content,
                    }
                    blocks.append(code_block)

                    # 남은 콘텐츠가 있으면 처리
                    if remaining_content:
                        current_block_lines.append(remaining_content)
                else:
                    # 닫는 태그가 다른 줄에 있음
                    code_lines = []
                    if content_after_start:
                        code_lines.append(content_after_start)

                    # }}} 태그를 찾을 때까지 계속
                    i += 1
                    while i < len(lines):
                        line = lines[i]
                        end_match = PlainTextBlockParser.CODE_END_PATTERN.match(line)
                        if end_match:
                            # 닫는 태그 앞의 내용
                            content_before_end = end_match.group(1)
                            if content_before_end:
                                code_lines.append(content_before_end)
                            remaining_content = end_match.group(2)

                            # 코드 블록 생성
                            code_content = '\n'.join(code_lines)
                            code_block = {
                                'type': 'code',
                                'content': code_content,
                            }
                            blocks.append(code_block)

                            # 남은 콘텐츠가 있으면 처리
                            if remaining_content.strip():
                                current_block_lines.append(remaining_content)
                            break
                        else:
                            code_lines.append(line)
                        i += 1

                i += 1
                continue

            # 현재 줄이 nowiki 시작인지 확인
            nowiki_start_match = PlainTextBlockParser.NOWIKI_START_PATTERN.match(line)
            if nowiki_start_match:
                # 누적된 블록을 먼저 처리
                if current_block_lines:
                    block_content = '\n'.join(current_block_lines)
                    if not PlainTextBlockParser._is_metadata_line(block_content):
                        block = PlainTextBlockParser._create_block(block_content)
                        blocks.append(block)
                    current_block_lines = []
                    in_list = False

                # 시작 태그 이후의 콘텐츠
                content_after_start = nowiki_start_match.group(1)

                # 닫는 태그가 같은 줄에 있는지 확인
                end_match = PlainTextBlockParser.NOWIKI_END_PATTERN.match(content_after_start)
                if end_match:
                    # 같은 줄에 <nowiki>content</nowiki> 형식
                    nowiki_content = end_match.group(1)
                    remaining_content = end_match.group(2)

                    # nowiki 블록 생성
                    nowiki_block = {
                        'type': 'nowiki',
                        'content': nowiki_content,
                    }
                    blocks.append(nowiki_block)

                    # 남은 콘텐츠가 있으면 처리
                    if remaining_content:
                        current_block_lines.append(remaining_content)
                else:
                    # 닫는 태그가 다른 줄에 있음
                    nowiki_lines = []
                    if content_after_start:
                        nowiki_lines.append(content_after_start)

                    # </nowiki> 태그를 찾을 때까지 계속
                    i += 1
                    while i < len(lines):
                        line = lines[i]
                        end_match = PlainTextBlockParser.NOWIKI_END_PATTERN.match(line)
                        if end_match:
                            # 닫는 태그 앞의 내용
                            content_before_end = end_match.group(1)
                            if content_before_end:
                                nowiki_lines.append(content_before_end)
                            remaining_content = end_match.group(2)

                            # nowiki 블록 생성
                            nowiki_content = '\n'.join(nowiki_lines)
                            nowiki_block = {
                                'type': 'nowiki',
                                'content': nowiki_content,
                            }
                            blocks.append(nowiki_block)

                            # 남은 콘텐츠가 있으면 처리
                            if remaining_content.strip():
                                current_block_lines.append(remaining_content)
                            break
                        else:
                            nowiki_lines.append(line)
                        i += 1

                i += 1
                continue

            if line.strip():
                # 현재 줄이 제목인지 확인
                heading_match = PlainTextBlockParser.HEADING_PATTERN.match(line)
                # 현재 줄이 수평선인지 확인
                horizontal_rule_match = PlainTextBlockParser.HORIZONTAL_RULE_PATTERN.match(line.strip())
                # 현재 줄이 줄 바꿈 매크로인지 확인
                line_break_match = PlainTextBlockParser.LINE_BREAK_PATTERN.match(line.strip())
                # 현재 줄이 순서 없는 목록 항목인지 확인
                unordered_list_match = PlainTextBlockParser.UNORDERED_LIST_PATTERN.match(line)
                # 현재 줄이 순서 있는 목록 항목인지 확인
                ordered_list_match = PlainTextBlockParser.ORDERED_LIST_PATTERN.match(line)
                # 현재 줄이 테이블 행인지 확인
                table_row_match = PlainTextBlockParser.TABLE_ROW_PATTERN.match(line)

                if heading_match:
                    # 누적된 블록을 먼저 처리
                    if current_block_lines:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵 (예: [[Category:...]], [[Redirect:...]])
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []
                        in_list = False

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
                elif horizontal_rule_match:
                    # 누적된 블록을 먼저 처리
                    if current_block_lines:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []
                        in_list = False

                    # 수평선 블록 생성
                    horizontal_rule_block = {
                        'type': 'horizontal_rule',
                    }
                    blocks.append(horizontal_rule_block)
                elif line_break_match:
                    # 누적된 블록을 먼저 처리
                    if current_block_lines:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []
                        in_list = False

                    # 줄 바꿈 블록 생성
                    line_break_block = {
                        'type': 'line_break',
                    }
                    blocks.append(line_break_block)
                elif unordered_list_match or ordered_list_match:
                    # 현재 비-목록 블록이 있으면 먼저 처리
                    if current_block_lines and not in_list:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []

                    # 목록 줄을 현재 블록에 추가
                    current_block_lines.append(line)
                    in_list = True
                elif table_row_match:
                    # 현재 비-테이블 블록이 있으면 먼저 처리
                    if current_block_lines and not in_table:
                        block_content = '\n'.join(current_block_lines)
                        # 메타데이터 줄은 스킵
                        if not PlainTextBlockParser._is_metadata_line(block_content):
                            block = PlainTextBlockParser._create_block(block_content)
                            blocks.append(block)
                        current_block_lines = []
                        in_list = False

                    # 테이블 행을 현재 블록에 추가
                    current_block_lines.append(line)
                    in_table = True
                else:
                    # 현재 목록 또는 테이블 블록이 있으면 먼저 처리
                    if current_block_lines and (in_list or in_table):
                        block_content = '\n'.join(current_block_lines)
                        block = PlainTextBlockParser._create_block(block_content)
                        blocks.append(block)
                        current_block_lines = []
                        in_list = False
                        in_table = False

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
                    in_list = False
                    in_table = False

            i += 1

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
        # 테이블 블록인지 확인
        if PlainTextBlockParser._is_table(content):
            return PlainTextBlockParser._create_table_block(content)

        # 순서 없는 목록 블록인지 확인
        if PlainTextBlockParser._is_unordered_list(content):
            return PlainTextBlockParser._create_unordered_list_block(content)

        # 순서 있는 목록 블록인지 확인
        if PlainTextBlockParser._is_ordered_list(content):
            return PlainTextBlockParser._create_ordered_list_block(content)

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

        메타데이터 줄은 [[Category:...]], [[Redirect:...]], [[Backlink:...]] 등의 형식이다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            메타데이터 줄이면 True
        """
        lines = content.split('\n')
        for line in lines:
            # 모든 줄이 메타데이터 형식이어야 함
            if not re.match(r'^\[\[(?:Category|Redirect|Backlink):', line):
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

        제목, 링크, 카테고리, 리다이렉트, 외부 링크, 백링크를 메타데이터로 추출한다.

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
        backlinks = []
        main_heading = None

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
            elif line.startswith('[[Backlink:') and line.endswith(']]'):
                backlink_name = line[len('[[Backlink:'):-2]
                backlinks.append(backlink_name)

        # 블록에서 메타데이터 추출
        for block in blocks:
            if block.get('type') == 'heading':
                heading_info = {
                    'level': block['level'],
                    'text': block['content'],
                }
                headings.append(heading_info)
                # 첫 번째 레벨 1 제목을 main heading으로 저장
                if main_heading is None and block['level'] == 1:
                    main_heading = block['content']
            elif block.get('type') == 'paragraph':
                # 문단에서 내부 링크 추출
                content = block.get('content', '')
                extracted_links, extracted_categories, extracted_redirects, extracted_backlinks = \
                    PlainTextBlockParser._extract_links_from_content(content)
                links.extend(extracted_links)
                categories.extend(extracted_categories)
                redirects.extend(extracted_redirects)
                backlinks.extend(extracted_backlinks)
                # 문단에서 외부 링크 추출
                extracted_external_links = PlainTextBlockParser._extract_external_links_from_content(content)
                external_links.extend(extracted_external_links)

        # 중복 제거하되 순서 유지
        links = list(dict.fromkeys(links))
        categories = list(dict.fromkeys(categories))
        external_links = list(dict.fromkeys(external_links))
        backlinks = list(dict.fromkeys(backlinks))

        # 리다이렉트의 "from" 필드를 main heading으로 설정
        if redirects and main_heading:
            for redirect in redirects:
                if redirect['from'] == '':
                    redirect['from'] = main_heading

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

        # backlinks가 있으면 추가
        if backlinks:
            metadata['backlinks'] = backlinks

        return metadata

    @staticmethod
    def _extract_links_from_content(content: str) -> tuple:
        """
        콘텐츠에서 내부 링크, 카테고리, 리다이렉트, 백링크를 추출한다.

        내부 링크 형식:
        - [[LinkName]] - 일반 링크
        - [[Category:Name]] - 카테고리
        - [[Redirect:Name]] - 리다이렉트
        - [[Backlink:Name]] - 백링크

        Args:
            content: 파싱할 콘텐츠

        Returns:
            (links, categories, redirects, backlinks) 튜플
        """
        links = []
        categories = []
        redirects = []
        backlinks = []

        matches = PlainTextBlockParser.INTERNAL_LINK_PATTERN.findall(content)
        for match in matches:
            if match.startswith('Category:'):
                category_name = match[len('Category:'):]
                categories.append(category_name)
            elif match.startswith('Redirect:'):
                redirect_target = match[len('Redirect:'):]
                redirects.append({'from': '', 'to': redirect_target})
            elif match.startswith('Backlink:'):
                backlink_name = match[len('Backlink:'):]
                backlinks.append(backlink_name)
            else:
                # 일반 링크
                links.append(match)

        return links, categories, redirects, backlinks

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

    @staticmethod
    def _build_nested_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        평탄한 아이템 배열을 중첩된 구조로 변환한다.

        레벨이 높은 아이템들을 낮은 레벨의 부모 아이템 아래 children으로 배치한다.

        Args:
            items: 레벨 정보가 있는 평탄한 아이템 배열

        Returns:
            중첩된 구조의 아이템 배열
        """
        if not items:
            return []

        result = []
        stack = []  # (item, level) 튜플의 스택

        for item in items:
            current_level = item['level']
            current_item = item.copy()
            current_item['children'] = []

            # 스택에서 같거나 더 낮은 레벨의 아이템들을 제거
            while stack and stack[-1][1] >= current_level:
                stack.pop()

            # 부모 아이템에 추가
            if stack:
                stack[-1][0]['children'].append(current_item)
            else:
                # 루트 레벨 아이템
                result.append(current_item)

            # 현재 아이템을 스택에 추가
            stack.append((current_item, current_level))

        return result

    @staticmethod
    def _is_unordered_list(content: str) -> bool:
        """
        콘텐츠가 순서 없는 목록인지 확인한다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            순서 없는 목록이면 True
        """
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not PlainTextBlockParser.UNORDERED_LIST_PATTERN.match(line):
                # 한 줄이라도 목록 패턴과 일치하지 않으면 목록이 아님
                return False
        # 최소한 한 개 이상의 목록 줄이 있어야 함
        return any(PlainTextBlockParser.UNORDERED_LIST_PATTERN.match(line) for line in lines)

    @staticmethod
    def _create_unordered_list_block(content: str) -> Dict[str, Any]:
        """
        순서 없는 목록 블록을 생성한다.

        Args:
            content: 목록 콘텐츠

        Returns:
            목록 블록 딕셔너리
        """
        lines = content.split('\n')
        items = []

        for line in lines:
            match = PlainTextBlockParser.UNORDERED_LIST_PATTERN.match(line)
            if match:
                asterisks = match.group(1)
                text = match.group(2)
                level = len(asterisks)
                items.append({
                    'level': level,
                    'text': text,
                })

        # 평탄한 아이템 배열을 중첩된 구조로 변환
        nested_items = PlainTextBlockParser._build_nested_list(items)

        return {
            'type': 'list',
            'list_type': 'unordered',
            'items': nested_items,
        }

    @staticmethod
    def _is_ordered_list(content: str) -> bool:
        """
        콘텐츠가 순서 있는 목록인지 확인한다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            순서 있는 목록이면 True
        """
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not PlainTextBlockParser.ORDERED_LIST_PATTERN.match(line):
                # 한 줄이라도 목록 패턴과 일치하지 않으면 목록이 아님
                return False
        # 최소한 한 개 이상의 목록 줄이 있어야 함
        return any(PlainTextBlockParser.ORDERED_LIST_PATTERN.match(line) for line in lines)

    @staticmethod
    def _create_ordered_list_block(content: str) -> Dict[str, Any]:
        """
        순서 있는 목록 블록을 생성한다.

        Args:
            content: 목록 콘텐츠

        Returns:
            목록 블록 딕셔너리
        """
        lines = content.split('\n')
        items = []

        for line in lines:
            match = PlainTextBlockParser.ORDERED_LIST_PATTERN.match(line)
            if match:
                hashes = match.group(1)
                text = match.group(2)
                level = len(hashes)
                items.append({
                    'level': level,
                    'text': text,
                })

        # 평탄한 아이템 배열을 중첩된 구조로 변환
        nested_items = PlainTextBlockParser._build_nested_list(items)

        return {
            'type': 'list',
            'list_type': 'ordered',
            'items': nested_items,
        }

    @staticmethod
    def _is_table(content: str) -> bool:
        """
        콘텐츠가 테이블인지 확인한다.

        Args:
            content: 검사할 콘텐츠

        Returns:
            테이블이면 True
        """
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not PlainTextBlockParser.TABLE_ROW_PATTERN.match(line):
                # 한 줄이라도 테이블 패턴과 일치하지 않으면 테이블이 아님
                return False
        # 최소한 한 개 이상의 테이블 행이 있어야 함
        return any(PlainTextBlockParser.TABLE_ROW_PATTERN.match(line) for line in lines)

    @staticmethod
    def _create_table_block(content: str) -> Dict[str, Any]:
        """
        테이블 블록을 생성한다.

        Args:
            content: 테이블 콘텐츠

        Returns:
            테이블 블록 딕셔너리
        """
        lines = content.split('\n')
        rows = []

        for line in lines:
            match = PlainTextBlockParser.TABLE_ROW_PATTERN.match(line)
            if match:
                # ||로 구분된 셀 추출
                cells_content = match.group(1)
                # 빈 셀 처리를 위해 || 기반으로 분할
                cells = cells_content.split('||')
                # 빈 셀 제거 (시작/끝의 빈 셀)
                cells = [cell.strip() for cell in cells if cell.strip()]
                rows.append({'cells': cells})

        return {
            'type': 'table',
            'rows': rows,
        }
