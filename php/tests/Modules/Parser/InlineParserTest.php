<?php

declare(strict_types=1);

/**
 * InlineParser 테스트 (태스크 0704).
 *
 * NamuMark풍 인라인 문법 -> HTML 변환, 중첩, XSS 이스케이프, 짝이 맞지 않는
 * 마크업의 리터럴 폴백을 검증한다. 이 저장소의 관례(`assert()`가 아니라
 * 실패를 배열에 모아 마지막에 exit(1))를 따른다 — `zend.assertions`가
 * 기본값(off)인 환경에서도 실패를 확실히 감지하기 위함이다
 * (tests/Modules/Parser/ParityPlaceholderTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Parser\InlineParser;

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

$parser = new InlineParser();

// --- 굵게 ---
$result = $parser->parse("이것은 '''굵게''' 표시된 텍스트");
check($failures, $result->html() === '이것은 <strong>굵게</strong> 표시된 텍스트', "굵게 변환 실패: {$result->html()}");

// --- 기울임 ---
$result = $parser->parse("이것은 ''기울임'' 표시된 텍스트");
check($failures, $result->html() === '이것은 <em>기울임</em> 표시된 텍스트', "기울임 변환 실패: {$result->html()}");

// --- 밑줄 ---
$result = $parser->parse('__밑줄__');
check($failures, $result->html() === '<u>밑줄</u>', "밑줄 변환 실패: {$result->html()}");

// --- 취소선(물결) ---
$result = $parser->parse('~~취소선~~');
check($failures, $result->html() === '<del>취소선</del>', "취소선(~~) 변환 실패: {$result->html()}");

// --- 취소선(대시) ---
$result = $parser->parse('--취소선--');
check($failures, $result->html() === '<del>취소선</del>', "취소선(--) 변환 실패: {$result->html()}");

// --- 인라인 코드 ---
$result = $parser->parse('`echo 1`');
check($failures, $result->html() === '<code>echo 1</code>', "코드 변환 실패: {$result->html()}");

// --- 코드 내부는 마크업으로 해석되지 않고, 이스케이프된 리터럴로 남는다 ---
$result = $parser->parse("`'''not bold'''`");
check($failures, $result->html() === '<code>&#039;&#039;&#039;not bold&#039;&#039;&#039;</code>', "코드 내부가 리터럴로 유지되지 않음: {$result->html()}");

// --- 내부 링크(표시문구 없음) ---
$result = $parser->parse('[[문서제목]]');
check($failures, $result->html() === '<a href="/wiki/%EB%AC%B8%EC%84%9C%EC%A0%9C%EB%AA%A9">문서제목</a>', "내부 링크(표시문구 없음) 변환 실패: {$result->html()}");
check($failures, $result->links() === ['문서제목'], "내부 링크가 links()에 수집되지 않음: " . json_encode($result->links()));

// --- 내부 링크(표시문구 있음) ---
$result = $parser->parse('[[문서제목|표시문구]]');
check($failures, $result->html() === '<a href="/wiki/%EB%AC%B8%EC%84%9C%EC%A0%9C%EB%AA%A9">표시문구</a>', "내부 링크(표시문구 있음) 변환 실패: {$result->html()}");
check($failures, $result->links() === ['문서제목'], "표시문구가 있어도 원제목이 links()에 수집되어야 함: " . json_encode($result->links()));

// --- 내부 링크 href는 공백/특수문자를 URL-safe하게 인코딩한다 (표시문구는 원문 그대로 보여도 된다) ---
$result = $parser->parse('[[문서 이름/하위]]');
check($failures, strpos($result->html(), 'href="/wiki/' . rawurlencode('문서 이름/하위') . '"') !== false, "내부 링크 href가 rawurlencode 결과를 포함하지 않음: {$result->html()}");

// --- 외부 링크: [url] ---
$result = $parser->parse('[https://example.com]');
check($failures, $result->html() === '<a href="https://example.com" rel="noopener noreferrer">https://example.com</a>', "외부 링크([url]) 변환 실패: {$result->html()}");
check($failures, $result->links() === [], "외부 링크는 links()에 포함되지 않아야 함: " . json_encode($result->links()));

// --- 외부 링크: [url 표시문구] ---
$result = $parser->parse('[https://example.com 예시 사이트]');
check($failures, $result->html() === '<a href="https://example.com" rel="noopener noreferrer">예시 사이트</a>', "외부 링크([url label]) 변환 실패: {$result->html()}");

// --- 외부 링크: [[http://... 표시문구]] ---
$result = $parser->parse('[[https://example.com 예시 사이트]]');
check($failures, $result->html() === '<a href="https://example.com" rel="noopener noreferrer">예시 사이트</a>', "외부 링크([[url label]]) 변환 실패: {$result->html()}");

// --- 외부 링크: [[http://...|표시문구]] ---
$result = $parser->parse('[[https://example.com|예시 사이트]]');
check($failures, $result->html() === '<a href="https://example.com" rel="noopener noreferrer">예시 사이트</a>', "외부 링크([[url|label]]) 변환 실패: {$result->html()}");

// --- 중첩: 굵게 안의 내부 링크 ---
$result = $parser->parse("'''[[문서제목]]'''");
check($failures, $result->html() === '<strong><a href="/wiki/%EB%AC%B8%EC%84%9C%EC%A0%9C%EB%AA%A9">문서제목</a></strong>', "중첩(굵게+내부링크) 변환 실패: {$result->html()}");
check($failures, $result->links() === ['문서제목'], "중첩된 링크도 links()에 수집되어야 함: " . json_encode($result->links()));

// --- 중첩: 기울임 안의 굵게 ---
$result = $parser->parse("''기울임 안에 '''굵게''' 있음''");
check($failures, $result->html() === '<em>기울임 안에 <strong>굵게</strong> 있음</em>', "중첩(기울임+굵게) 변환 실패: {$result->html()}");

// --- XSS: 굵게 내용 이스케이프 ---
$result = $parser->parse("'''<script>alert(1)</script>'''");
check($failures, strpos($result->html(), '<script>') === false, "굵게 내용의 <script> 태그가 이스케이프되지 않음: {$result->html()}");
check($failures, $result->html() === '<strong>&lt;script&gt;alert(1)&lt;/script&gt;</strong>', "굵게 내용 이스케이프 결과가 예상과 다름: {$result->html()}");

// --- XSS: 일반 텍스트의 특수문자 이스케이프 ---
$result = $parser->parse('<b onmouseover="alert(1)">텍스트</b> & "따옴표" \'작은따옴표\'');
check($failures, strpos($result->html(), '<b ') === false, "일반 텍스트의 원본 태그가 이스케이프 없이 남음: {$result->html()}");
check($failures, strpos($result->html(), '&lt;b') !== false, "< 문자가 이스케이프되지 않음: {$result->html()}");
check($failures, strpos($result->html(), '&amp;') !== false, "& 문자가 이스케이프되지 않음: {$result->html()}");
check($failures, strpos($result->html(), '&quot;') !== false, "큰따옴표가 이스케이프되지 않음: {$result->html()}");

// --- XSS: 내부 링크 제목/표시문구에 담긴 마크업 이스케이프 ---
$result = $parser->parse('[[<script>alert(1)</script>|표시<b>문구</b>]]');
check($failures, strpos($result->html(), '<script>') === false, "내부 링크 제목의 <script>가 이스케이프되지 않음: {$result->html()}");
check($failures, strpos($result->html(), '<b>') === false, "내부 링크 표시문구의 <b>가 이스케이프되지 않음: {$result->html()}");

// --- XSS: 외부 링크 URL에 담긴 따옴표가 속성을 깨지 않는다 ---
$result = $parser->parse('[https://example.com/"><script>alert(1)</script>]');
check($failures, strpos($result->html(), '<script>') === false, "외부 링크 URL의 <script>가 이스케이프되지 않음: {$result->html()}");
check($failures, strpos($result->html(), '"><script>') === false, "외부 링크 URL의 따옴표가 속성을 깨뜨림: {$result->html()}");

// --- 경계 케이스: 짝이 맞지 않는 굵게는 리터럴로 남는다 ---
$result = $parser->parse("이것은 '''닫히지 않은 굵게 표시");
check($failures, $result->html() === "이것은 &#039;&#039;&#039;닫히지 않은 굵게 표시", "짝이 맞지 않는 굵게가 리터럴로 처리되지 않음: {$result->html()}");

// --- 경계 케이스: 짝이 맞지 않는 내부 링크 대괄호는 리터럴로 남고, 그 안의 완결된 링크는 처리된다 ---
$result = $parser->parse('[[Link1 and [[Link2]] only one closed.');
check($failures, strpos($result->html(), '<a href="/wiki/Link2">Link2</a>') !== false, "중첩된 완결 링크가 처리되지 않음: {$result->html()}");
check($failures, $result->links() === ['Link2'], "짝이 맞지 않는 바깥쪽 대괄호는 링크로 집계되지 않아야 함: " . json_encode($result->links()));

// --- 경계 케이스: 빈 소스 ---
$result = $parser->parse('');
check($failures, $result->html() === '', "빈 소스는 빈 HTML을 반환해야 함: {$result->html()}");
check($failures, $result->links() === [], "빈 소스는 빈 링크 목록을 반환해야 함: " . json_encode($result->links()));

if ($failures !== []) {
    fwrite(STDERR, "InlineParser 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InlineParser 테스트 통과.\n");
exit(0);
