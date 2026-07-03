<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\ResponsiveTable`의 동작을 확인하는 smoke test (태스크 0551).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 반응형 테이블이 올바르게 렌더링되는지
 * 확인한다. 테이블 구조, 헤더, 바디, 캡션이 올바르게 표시되어야 한다.
 * 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\ResponsiveTable;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper 생성
$escaper = new Escaper();
$table = new ResponsiveTable($escaper);

// (1) 빈 테이블 렌더링 (캡션 없음)
$columns = [
    ['key' => 'id', 'label' => 'ID'],
    ['key' => 'name', 'label' => '이름'],
];
$emptyRows = [];
$html = $table->render($columns, $emptyRows);

if (!str_contains($html, '<table class="responsive-table">')) {
    $failures[] = '테이블이 responsive-table 클래스를 가져야 한다.';
}

if (!str_contains($html, '<thead>')) {
    $failures[] = '테이블이 thead 요소를 포함해야 한다.';
}

if (!str_contains($html, '<tbody>')) {
    $failures[] = '테이블이 tbody 요소를 포함해야 한다.';
}

if (!str_contains($html, '<th scope="col">ID</th>')) {
    $failures[] = '테이블이 ID 헤더를 포함해야 한다.';
}

if (!str_contains($html, '<th scope="col">이름</th>')) {
    $failures[] = '테이블이 이름 헤더를 포함해야 한다.';
}

if (!str_contains($html, '<div class="responsive-table-wrapper">')) {
    $failures[] = '테이블이 responsive-table-wrapper div를 포함해야 한다.';
}

// (2) 데이터가 있는 테이블 렌더링
$rows = [
    ['id' => '1', 'name' => '사용자1'],
    ['id' => '2', 'name' => '사용자2'],
];
$htmlWithData = $table->render($columns, $rows);

if (!str_contains($htmlWithData, '<td data-column="id">1</td>')) {
    $failures[] = '테이블이 데이터 셀에 data-column 속성을 포함해야 한다.';
}

if (!str_contains($htmlWithData, '<td data-column="name">사용자1</td>')) {
    $failures[] = '테이블이 모든 데이터를 올바르게 렌더링해야 한다.';
}

if (!str_contains($htmlWithData, '<td data-column="id">2</td>')) {
    $failures[] = '테이블이 모든 행을 렌더링해야 한다.';
}

if (!str_contains($htmlWithData, '<td data-column="name">사용자2</td>')) {
    $failures[] = '테이블이 모든 데이터 행을 렌더링해야 한다.';
}

// (3) 캡션 있는 테이블 렌더링
$htmlWithCaption = $table->render($columns, $rows, '사용자 목록');

if (!str_contains($htmlWithCaption, '<caption>사용자 목록</caption>')) {
    $failures[] = '테이블이 캡션을 렌더링해야 한다.';
}

// (4) XSS 공격 방지 확인 - 헤더에서
$xssColumns = [
    ['key' => 'id', 'label' => '<script>alert("xss")</script>'],
    ['key' => 'name', 'label' => 'Name'],
];
$xssHtml = $table->render($xssColumns, []);

if (str_contains($xssHtml, '<script>')) {
    $failures[] = '헤더의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '헤더가 escape되어야 한다.';
}

// (5) XSS 공격 방지 확인 - 데이터에서
$xssRows = [
    ['id' => '<img src=x>', 'name' => '<img src=x onerror=alert("xss")>'],
];
$xssHtmlData = $table->render($columns, $xssRows);

if (str_contains($xssHtmlData, '<img src=x>')) {
    $failures[] = '데이터의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssHtmlData, '&lt;img src=x&gt;')) {
    $failures[] = '데이터의 특수 문자가 escape되어야 한다.';
}

// (6) XSS 공격 방지 확인 - 캡션에서
$xssCaption = '제목 <script>alert("xss")</script>';
$xssHtmlCaption = $table->render($columns, [], $xssCaption);

if (str_contains($xssHtmlCaption, '<script>')) {
    $failures[] = '캡션의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssHtmlCaption, '&lt;script&gt;')) {
    $failures[] = '캡션이 escape되어야 한다.';
}

// (7) 빈 컬럼 배열 처리
$emptyColumns = [];
$emptyColumnHtml = $table->render($emptyColumns, $rows);

if ($emptyColumnHtml !== '') {
    $failures[] = '컬럼이 없으면 빈 문자열을 반환해야 한다.';
}

// (8) data-column 속성에 XSS 방지 확인
$dataColumnXssRows = [
    ['id' => 'test', 'name' => 'test'],
];
$dataColumnXssColumns = [
    ['key' => '<script>', 'label' => 'Label'],
];
$dataColumnXssHtml = $table->render($dataColumnXssColumns, $dataColumnXssRows);

if (str_contains($dataColumnXssHtml, 'data-column="<')) {
    $failures[] = 'data-column 속성도 escape되어야 한다.';
}

if (!str_contains($dataColumnXssHtml, 'data-column="&lt;script&gt;"')) {
    $failures[] = 'data-column 속성의 특수 문자가 escape되어야 한다.';
}

// (9) 특수 문자 escape 확인
$specialRows = [
    ['id' => 'user & id', 'name' => '이름 & 성 < 기호'],
];
$specialHtml = $table->render($columns, $specialRows);

if (!str_contains($specialHtml, 'user &amp; id')) {
    $failures[] = '데이터의 & 문자가 escape되어야 한다.';
}

if (!str_contains($specialHtml, '&lt;')) {
    $failures[] = '데이터의 < 문자가 escape되어야 한다.';
}

// (10) 숫자 데이터 처리
$numRows = [
    ['id' => '123', 'name' => '456'],
];
$numHtml = $table->render($columns, $numRows);

if (!str_contains($numHtml, '<td data-column="id">123</td>')) {
    $failures[] = '테이블이 숫자 데이터를 올바르게 처리해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ResponsiveTable 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ResponsiveTable 테스트 통과.\n");
exit(0);
