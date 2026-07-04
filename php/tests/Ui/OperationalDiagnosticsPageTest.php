<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\OperationalDiagnosticsPage`의 동작을 확인하는 smoke test (태스크 0590).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 운영 진단 page가 올바르게 렌더링되는지
 * 확인한다. DB, 스키마, 캐시, 환경 진단 export 섹션이 표시되어야 한다.
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

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new OperationalDiagnosticsPage($escaper, $layout);

// (1) 기본 운영 진단 page 렌더링
$html = $page->render();

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

if (!str_contains($html, '<a href="/admin/status/file-permissions">파일 권한 진단 보기</a>')) {
    $failures[] = '운영 진단 page가 파일 권한 진단 page 링크를 포함해야 한다.';
}

if (!str_contains($html, '<button type="button" disabled>진단 export 준비 중</button>')) {
    $failures[] = '운영 진단 page가 비활성화된 환경 진단 export placeholder 버튼을 포함해야 한다.';
}

if (!str_contains($html, '민감 정보는 export 대상에서 제외됩니다.')) {
    $failures[] = '운영 진단 page가 민감 정보 제외 안내를 포함해야 한다.';
}

$versionFile = __DIR__ . '/../../VERSION';
$appVersion = trim((string) file_get_contents($versionFile));

if (!str_contains($html, '<dt>버전</dt><dd>' . $appVersion . '</dd>')) {
    $failures[] = '운영 진단 page가 VERSION 파일의 앱 버전을 표시해야 한다.';
}

if (!str_contains($html, '<th scope="row">APP_VERSION</th>')) {
    $failures[] = '환경 진단 export preview가 APP_VERSION 항목을 포함해야 한다.';
}

if (!str_contains($html, '<td>' . $appVersion . '</td>')) {
    $failures[] = '환경 진단 export preview가 앱 버전을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '운영 진단 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '운영 진단 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '운영 진단 page가 footer landmark를 포함해야 한다.';
}

// (2) Placeholder가 포함되어 있는지 확인
if (!str_contains($html, 'placeholder')) {
    $failures[] = '운영 진단 page가 placeholder를 포함해야 한다.';
}

// (3) 환경 진단 export preview에서 민감 정보가 제외되고 안전한 값은 escape되는지 확인
$exportHtml = $page->render([
    'PHP_VERSION' => '8.3.<safe>',
    'DB_PASSWORD' => 'super-secret-password',
    'APP_SECRET' => 'hidden-secret',
    'API_KEY' => 'hidden-api-key',
    'APP_KEY' => 'hidden-app-key',
    'SESSION_COOKIE' => 'hidden-cookie',
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

// (4) 애플리케이션 버전 표시가 escape되는지 확인
$escapedVersionPage = new OperationalDiagnosticsPage($escaper, $layout, '1.2.<safe>');
$escapedVersionHtml = $escapedVersionPage->render();

if (!str_contains($escapedVersionHtml, '<dt>버전</dt><dd>1.2.&lt;safe&gt;</dd>')) {
    $failures[] = '운영 진단 page가 앱 버전을 escape해서 표시해야 한다.';
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
