<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\OperationalDiagnosticsPage`의 동작을 확인하는 smoke test
 * (태스크 0590, 실데이터 렌더링 검증은 0717).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 운영 진단 page가 DB/스키마/캐시/
 * 환경 진단 실데이터를 렌더링하고(하드코딩 placeholder 문자열 없음),
 * 민감 정보를 제외하며, DB 미연결 상태에서도 안전하게 "미설정"으로
 * 표시하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\OperationalDiagnosticsPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$page = new OperationalDiagnosticsPage($escaper, $layout);

// (1) DB 연결됨/스키마 적용됨/캐시 사용 가능 상태의 실데이터 렌더링.
$connectedDiagnostics = [
    'db' => ['status' => '연결됨', 'version' => 'mysql 10.11.2-MariaDB'],
    'schema' => ['status' => '적용됨', 'migration' => '0717'],
    'cache' => ['status' => '사용 가능', 'usage' => 'file:/var/www/storage/cache'],
    'environment' => [
        'APP_VERSION' => '1.2.3',
        'PHP_VERSION' => PHP_VERSION,
        'PHP_SAPI' => PHP_SAPI,
        'APP_ENV' => 'production',
    ],
];
$html = $page->render($connectedDiagnostics);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '운영 진단 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>운영 진단</title>')) {
    $failures[] = '운영 진단 page의 title이 "운영 진단"이어야 한다.';
}

if (!str_contains($html, '<h1>운영 진단</h1>')) {
    $failures[] = '운영 진단 page가 h1으로 "운영 진단"을 표시해야 한다.';
}

if (!str_contains($html, '<h2>데이터베이스</h2>')) {
    $failures[] = '운영 진단 page가 "데이터베이스" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<h2>애플리케이션</h2>')) {
    $failures[] = '운영 진단 page가 "애플리케이션" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<h2>스키마</h2>')) {
    $failures[] = '운영 진단 page가 "스키마" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<h2>캐시</h2>')) {
    $failures[] = '운영 진단 page가 "캐시" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<h2>파일 권한</h2>')) {
    $failures[] = '운영 진단 page가 "파일 권한" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<h2>환경 진단 export</h2>')) {
    $failures[] = '운영 진단 page가 "환경 진단 export" 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="데이터베이스 상태">')) {
    $failures[] = '운영 진단 page가 데이터베이스 상태 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="애플리케이션 버전">')) {
    $failures[] = '운영 진단 page가 애플리케이션 버전 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="스키마 상태">')) {
    $failures[] = '운영 진단 page가 스키마 상태 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="캐시 상태">')) {
    $failures[] = '운영 진단 page가 캐시 상태 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="파일 권한 진단">')) {
    $failures[] = '운영 진단 page가 파일 권한 진단 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="환경 진단 export">')) {
    $failures[] = '운영 진단 page가 환경 진단 export 섹션을 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/diagnostics/files">파일 권한 진단 보기</a>')) {
    $failures[] = '운영 진단 page가 파일 권한 진단 page 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/diagnostics/export">환경 진단 export 다운로드</a>')) {
    $failures[] = '운영 진단 page가 환경 진단 export 다운로드 링크를 포함해야 한다.';
}

if (str_contains($html, 'disabled')) {
    $failures[] = '운영 진단 page가 더 이상 비활성화된 export 버튼을 포함하면 안 된다.';
}

if (!str_contains($html, '민감 정보는 export 대상에서 제외됩니다.')) {
    $failures[] = '운영 진단 page가 민감 정보 제외 안내를 포함해야 한다.';
}

// (1) DB/스키마/캐시 실데이터 값이 실제로 렌더링되는지 확인.
if (!str_contains($html, '<dt>상태</dt><dd>연결됨</dd>')) {
    $failures[] = '운영 진단 page가 DB 연결 상태를 표시해야 한다.';
}

if (!str_contains($html, '<dt>버전</dt><dd>mysql 10.11.2-MariaDB</dd>')) {
    $failures[] = '운영 진단 page가 DB 드라이버/서버 버전을 표시해야 한다.';
}

if (!str_contains($html, '<dt>상태</dt><dd>적용됨</dd>')) {
    $failures[] = '운영 진단 page가 스키마 적용 상태를 표시해야 한다.';
}

if (!str_contains($html, '<dt>마이그레이션</dt><dd>0717</dd>')) {
    $failures[] = '운영 진단 page가 최신 스키마 버전을 표시해야 한다.';
}

if (!str_contains($html, '<dt>상태</dt><dd>사용 가능</dd>')) {
    $failures[] = '운영 진단 page가 캐시 상태를 표시해야 한다.';
}

if (!str_contains($html, '<dt>사용 현황</dt><dd>file:/var/www/storage/cache</dd>')) {
    $failures[] = '운영 진단 page가 캐시 사용 현황을 표시해야 한다.';
}

if (!str_contains($html, '<th scope="row">APP_ENV</th>')) {
    $failures[] = '운영 진단 page의 export preview가 APP_ENV 항목을 포함해야 한다.';
}

if (!str_contains($html, '<td>production</td>')) {
    $failures[] = '운영 진단 page의 export preview가 실제 APP_ENV 값을 표시해야 한다.';
}

// (2) 하드코딩 placeholder 문자열이 완전히 사라졌는지 확인.
if (str_contains($html, 'placeholder')) {
    $failures[] = '운영 진단 page가 더 이상 placeholder 문자열을 포함하면 안 된다.';
}

// (3) DB 미연결(미설정/오류) 상태에서도 안전하게 표시되는지 확인.
$disconnectedDiagnostics = [
    'db' => ['status' => '미설정', 'version' => '-'],
    'schema' => ['status' => '확인 불가', 'migration' => '-'],
    'cache' => ['status' => '접근 불가', 'usage' => 'file:/var/www/storage/cache'],
    'environment' => [
        'APP_VERSION' => '1.2.3',
        'PHP_VERSION' => PHP_VERSION,
        'PHP_SAPI' => PHP_SAPI,
        'APP_ENV' => 'production',
    ],
];
$disconnectedHtml = $page->render($disconnectedDiagnostics);

if (!str_contains($disconnectedHtml, '<dt>상태</dt><dd>미설정</dd>')) {
    $failures[] = 'DB 미설정 상태에서 운영 진단 page가 "미설정"을 표시해야 한다.';
}

if (str_contains($disconnectedHtml, 'placeholder')) {
    $failures[] = 'DB 미설정 상태에서도 placeholder 문자열을 포함하면 안 된다.';
}

// (4) 인자 없이 render()를 호출해도(직접 인스턴스화하는 다른 호출자) 죽지 않고
// 안전한 기본값으로 대체되는지 확인 — placeholder 문자열은 여전히 없어야 한다.
$defaultHtml = $page->render();
if (str_contains($defaultHtml, 'placeholder')) {
    $failures[] = '인자 없는 render() 호출도 placeholder 문자열을 포함하면 안 된다.';
}

// (5) 환경 진단 export preview에서 민감 정보가 제외되고 안전한 값은 escape되는지 확인.
$exportHtml = $page->render([
    'environment' => [
        'PHP_VERSION' => '8.3.<safe>',
        'DB_PASSWORD' => 'super-secret-password',
        'APP_SECRET' => 'hidden-secret',
        'API_KEY' => 'hidden-api-key',
        'APP_KEY' => 'hidden-app-key',
        'SESSION_COOKIE' => 'hidden-cookie',
        'DATABASE_URL' => 'mysql://user:hidden-dsn-password@localhost/db',
    ],
]);

$sensitiveTexts = [
    'DB_PASSWORD',
    'super-secret-password',
    'APP_SECRET',
    'hidden-secret',
    'API_KEY',
    'hidden-api-key',
    'APP_KEY',
    'hidden-app-key',
    'SESSION_COOKIE',
    'hidden-cookie',
    'DATABASE_URL',
    'hidden-dsn-password',
];

foreach ($sensitiveTexts as $sensitiveText) {
    if (str_contains($exportHtml, $sensitiveText)) {
        $failures[] = "환경 진단 export preview가 민감 정보 {$sensitiveText}를 제외해야 한다.";
    }
}

if (!str_contains($exportHtml, 'PHP_VERSION')) {
    $failures[] = '환경 진단 export preview가 민감하지 않은 항목 이름을 포함해야 한다.';
}

if (!str_contains($exportHtml, '8.3.&lt;safe&gt;')) {
    $failures[] = '환경 진단 export preview가 민감하지 않은 값을 escape해서 표시해야 한다.';
}

// (6) 애플리케이션 버전 표시가 escape되는지 확인.
$escapedVersionPage = new OperationalDiagnosticsPage($escaper, $layout, '1.2.<safe>');
$escapedVersionHtml = $escapedVersionPage->render($connectedDiagnostics);

if (!str_contains($escapedVersionHtml, '<dt>버전</dt><dd>1.2.&lt;safe&gt;</dd>')) {
    $failures[] = '운영 진단 page가 앱 버전을 escape해서 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '운영 진단 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '운영 진단 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '운영 진단 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "OperationalDiagnosticsPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "OperationalDiagnosticsPage 테스트 통과.\n");
exit(0);
