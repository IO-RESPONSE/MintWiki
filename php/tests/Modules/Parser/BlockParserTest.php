<?php

declare(strict_types=1);

/**
 * BlockParser 테스트 (태스크 0705).
 *
 * NamuMark풍 블록 문법(제목/목록/표/구분선/인용/문단) -> HTML 변환, 제목
 * 앵커 id 수집(headings()), 인라인 파서(0704)와의 조합, XSS 이스케이프를
 * 검증한다. 이 저장소의 관례(`assert()`가 아니라 실패를 배열에 모아 마지막에
 * exit(1))를 따른다(tests/Modules/Parser/InlineParserTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Parser\BlockParser;

/** @var list<string> $failures */
$failures = [];

/**
 * @param list<string> $failures
 */
function check(array &$failures, bool $condition, string $message): void
{
    if (!$condition) {
        $failures[] = $message;
    }
}

$parser = new BlockParser();

// --- 제목: 레벨 1(==)~5(======) -> h2~h6, 앵커 id 수집 ---
$result = $parser->parse('== 소개 ==');
check($failures, $result->html() === '<h2 id="소개">소개</h2>', "레벨1 제목 변환 실패: {$result->html()}");
check($failures, $result->headings() === [['level' => 1, 'text' => '소개', 'id' => '소개']], "레벨1 제목이 headings()에 수집되지 않음: " . json_encode($result->headings(), JSON_UNESCAPED_UNICODE));

$result = $parser->parse('====== 세부 ======');
check($failures, $result->html() === '<h6 id="세부">세부</h6>', "레벨5 제목 변환 실패: {$result->html()}");
check($failures, $result->headings() === [['level' => 5, 'text' => '세부', 'id' => '세부']], "레벨5 제목이 headings()에 수집되지 않음: " . json_encode($result->headings(), JSON_UNESCAPED_UNICODE));

// --- 제목 안의 인라인 마크업은 렌더링되고, headings()의 text/앵커 id는 마크업 기호가 빠진 순수 텍스트다 ---
$result = $parser->parse("== '''굵은''' 제목 ==");
check($failures, $result->html() === '<h2 id="굵은-제목"><strong>굵은</strong> 제목</h2>', "제목 안 인라인 마크업 변환 실패: {$result->html()}");
check($failures, $result->headings() === [['level' => 1, 'text' => '굵은 제목', 'id' => '굵은-제목']], "제목 label/앵커 id가 마크업 기호를 걷어내지 못함: " . json_encode($result->headings(), JSON_UNESCAPED_UNICODE));

// --- 제목 중복 시 앵커 id에 -2, -3 접미사 ---
$result = $parser->parse("== 개요 ==\n\n== 개요 ==\n\n== 개요 ==");
check($failures, $result->headings() === [
    ['level' => 1, 'text' => '개요', 'id' => '개요'],
    ['level' => 1, 'text' => '개요', 'id' => '개요-2'],
    ['level' => 1, 'text' => '개요', 'id' => '개요-3'],
], "중복 제목의 앵커 id suffix 처리 실패: " . json_encode($result->headings(), JSON_UNESCAPED_UNICODE));

// --- 순서없는 목록(중첩 포함) ---
$result = $parser->parse("* 첫째\n** 첫째의 하위\n* 둘째");
check($failures, $result->html() === '<ul><li>첫째<ul><li>첫째의 하위</li></ul></li><li>둘째</li></ul>', "중첩 목록 변환 실패: {$result->html()}");

// --- 순서있는 목록 ---
$result = $parser->parse("1. 하나\n2. 둘\n3. 셋");
check($failures, $result->html() === '<ol><li>하나</li><li>둘</li><li>셋</li></ol>', "순서있는 목록 변환 실패: {$result->html()}");

// --- 표: 행/열 분리 + 셀 안 인라인 마크업 ---
$result = $parser->parse("||이름||나이||\n||''' 철수'''||20||");
check($failures, $result->html() === "<table><tr><td>이름</td><td>나이</td></tr><tr><td><strong> 철수</strong></td><td>20</td></tr></table>", "표 변환 실패: {$result->html()}");

// --- 구분선 ---
$result = $parser->parse('----');
check($failures, $result->html() === '<hr>', "구분선 변환 실패: {$result->html()}");

// --- 인용 (연속 줄은 하나의 blockquote로 묶임) ---
$result = $parser->parse("> 첫 줄\n> 둘째 줄");
check($failures, $result->html() === '<blockquote><p>첫 줄<br>둘째 줄</p></blockquote>', "인용 변환 실패: {$result->html()}");

// --- 문단: 빈 줄로 구분, 같은 문단 안 줄바꿈은 <br> ---
$result = $parser->parse("첫째 줄\n둘째 줄\n\n다른 문단");
check($failures, $result->html() === '<p>첫째 줄<br>둘째 줄</p><p>다른 문단</p>', "문단 분리 변환 실패: {$result->html()}");

// --- 문단 안 인라인 마크업 + 내부 링크가 문서 전체 links()에 수집됨 ---
$result = $parser->parse("'''굵게''' 그리고 [[문서제목]]");
check($failures, $result->html() === '<p><strong>굵게</strong> 그리고 <a href="/wiki/%EB%AC%B8%EC%84%9C%EC%A0%9C%EB%AA%A9">문서제목</a></p>', "문단 인라인 조합 변환 실패: {$result->html()}");
check($failures, $result->links() === ['문서제목'], "문단 내부 링크가 links()에 수집되지 않음: " . json_encode($result->links()));

// --- 여러 블록 조합: 제목 + 문단 + 목록 ---
$result = $parser->parse("== 제목 ==\n문단입니다.\n\n* 목록1\n* 목록2");
check($failures, $result->html() === '<h2 id="제목">제목</h2><p>문단입니다.</p><ul><li>목록1</li><li>목록2</li></ul>', "여러 블록 조합 변환 실패: {$result->html()}");
check($failures, $result->headings() === [['level' => 1, 'text' => '제목', 'id' => '제목']], "여러 블록 조합에서 headings() 수집 실패: " . json_encode($result->headings(), JSON_UNESCAPED_UNICODE));

// --- XSS: 문단의 리터럴 텍스트는 이스케이프된다 ---
$result = $parser->parse('<script>alert(1)</script>');
check($failures, strpos($result->html(), '<script>') === false, "문단의 <script>가 이스케이프되지 않음: {$result->html()}");
check($failures, $result->html() === '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>', "문단 이스케이프 결과가 예상과 다름: {$result->html()}");

// --- XSS: 제목의 리터럴 텍스트도 이스케이프된다 ---
$result = $parser->parse('== <script>alert(1)</script> ==');
check($failures, strpos($result->html(), '<script>alert') === false, "제목의 <script>가 이스케이프되지 않음: {$result->html()}");

// --- 경계 케이스: 빈 소스 ---
$result = $parser->parse('');
check($failures, $result->html() === '', "빈 소스는 빈 HTML을 반환해야 함: {$result->html()}");
check($failures, $result->headings() === [], "빈 소스는 빈 headings()를 반환해야 함: " . json_encode($result->headings()));

if ($failures !== []) {
    fwrite(STDERR, "BlockParser 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "BlockParser 테스트 통과.\n");
exit(0);
