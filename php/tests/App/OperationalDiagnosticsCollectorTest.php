<?php

declare(strict_types=1);

/**
 * `MintWiki\App\OperationalDiagnosticsCollector`의 동작을 확인하는 smoke test
 * (태스크 0717).
 *
 * DB 연결/미연결, 스키마 적용/미적용, 파일 캐시 접근 가능/불가능 상태를
 * sqlite in-memory PDO와 임시 디렉터리로 재현해 확인한다. 실제 값 조회가
 * 예외를 던지지 않고 항상 "미설정"/"오류" 등 안전한 문자열로 대체되는지가
 * 핵심이다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;
use MintWiki\App\OperationalDiagnosticsCollector;
use MintWiki\App\StoragePathConfig;

$failures = [];

// (1) DB 미설정 상태 — pdo=null, dbConnectionStatus='unconfigured'.
// StoragePathConfig::cachePath()는 storage root 아래 'cache' 하위 디렉터리를
// 가리키므로(예: <storageRoot>/cache), 실제로 존재/쓰기 가능해야 하는 경로는
// $storageRoot가 아니라 그 하위의 cache 디렉터리다.
$storageRoot = sys_get_temp_dir() . '/mintwiki-diagnostics-collector-test-' . getmypid();
$cacheDir = $storageRoot . '/cache';
@mkdir($cacheDir, 0775, true);

$unconfiguredCollector = new OperationalDiagnosticsCollector(
    null,
    'unconfigured',
    new ConfigLoader([]),
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
$unconfiguredDiagnostics = $unconfiguredCollector->collect();

if ($unconfiguredDiagnostics['db']['status'] !== '미설정') {
    $failures[] = '(1) DB 미설정 상태는 "미설정"으로 표시되어야 한다.';
}
if ($unconfiguredDiagnostics['schema']['status'] !== '확인 불가') {
    $failures[] = '(1) DB 미설정 상태에서 스키마는 "확인 불가"로 표시되어야 한다.';
}
if ($unconfiguredDiagnostics['cache']['status'] !== '사용 가능') {
    $failures[] = '(1) 쓰기 가능한 캐시 디렉터리는 "사용 가능"으로 표시되어야 한다.';
}

// (2) DB 오류 상태 — pdo=null, dbConnectionStatus='error'.
$errorCollector = new OperationalDiagnosticsCollector(
    null,
    'error',
    new ConfigLoader([]),
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
if ($errorCollector->collect()['db']['status'] !== '오류') {
    $failures[] = '(2) DB 접속 오류 상태는 "오류"로 표시되어야 한다.';
}

// (3) DB 연결됨 + 스키마 미적용(schema_version 테이블 없음).
$connectedNoSchemaPdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connectedNoSchemaCollector = new OperationalDiagnosticsCollector(
    $connectedNoSchemaPdo,
    'connected',
    new ConfigLoader([]),
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
$connectedNoSchemaDiagnostics = $connectedNoSchemaCollector->collect();

if ($connectedNoSchemaDiagnostics['db']['status'] !== '연결됨') {
    $failures[] = '(3) 연결된 PDO는 "연결됨"으로 표시되어야 한다.';
}
if (!str_contains($connectedNoSchemaDiagnostics['db']['version'], 'sqlite')) {
    $failures[] = '(3) DB 버전 문자열에 드라이버 이름(sqlite)이 포함되어야 한다.';
}
if ($connectedNoSchemaDiagnostics['schema']['status'] !== '미적용') {
    $failures[] = '(3) schema_version 테이블이 없으면 "미적용"으로 표시되어야 한다.';
}

// (4) DB 연결됨 + 스키마 적용됨(schema_version에 버전 행 존재).
$schemaSql = file_get_contents(__DIR__ . '/../../../db/schema/schema_version.sql');
if ($schemaSql === false) {
    fwrite(STDERR, "schema_version.sql fixture를 읽을 수 없습니다.\n");
    exit(1);
}
$connectedWithSchemaPdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connectedWithSchemaPdo->exec($schemaSql);
$connectedWithSchemaPdo->exec("INSERT INTO schema_version (version, applied_at) VALUES ('0716', '2026-07-01 00:00:00')");
$connectedWithSchemaPdo->exec("INSERT INTO schema_version (version, applied_at) VALUES ('0717', '2026-07-06 00:00:00')");

$connectedWithSchemaCollector = new OperationalDiagnosticsCollector(
    $connectedWithSchemaPdo,
    'connected',
    new ConfigLoader([]),
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
$connectedWithSchemaDiagnostics = $connectedWithSchemaCollector->collect();

if ($connectedWithSchemaDiagnostics['schema']['status'] !== '적용됨') {
    $failures[] = '(4) schema_version에 행이 있으면 "적용됨"으로 표시되어야 한다.';
}
if ($connectedWithSchemaDiagnostics['schema']['migration'] !== '0717') {
    $failures[] = '(4) 최신(applied_at 기준) schema_version이 반환되어야 한다.';
}

// (5) 캐시 디렉터리가 없으면(쓰기 불가) "접근 불가"로 표시된다.
$missingCacheDir = sys_get_temp_dir() . '/mintwiki-diagnostics-collector-test-missing-' . getmypid();
$unreachableCacheCollector = new OperationalDiagnosticsCollector(
    null,
    'unconfigured',
    new ConfigLoader([]),
    new StoragePathConfig(new ConfigLoader([]), $missingCacheDir),
    '1.2.3'
);
if ($unreachableCacheCollector->collect()['cache']['status'] !== '접근 불가') {
    $failures[] = '(5) 존재하지 않는 캐시 디렉터리는 "접근 불가"로 표시되어야 한다.';
}

// (6) redis_url이 설정되어 있으면 file 대신 redis 백엔드로 보고한다.
$redisConfiguredCollector = new OperationalDiagnosticsCollector(
    null,
    'unconfigured',
    new ConfigLoader(['redis_url' => 'redis://localhost:6379/0']),
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
$redisCacheDiagnostics = $redisConfiguredCollector->collect()['cache'];
if (!str_contains($redisCacheDiagnostics['usage'], 'redis')) {
    $failures[] = '(6) redis_url이 설정되면 캐시 사용 현황에 redis가 표시되어야 한다.';
}

// (7) export 스냅샷은 평면 문자열 map이고, DB 자격 증명 관련 key/값을 담지 않는다.
$exportConfigLoader = new ConfigLoader([
    'database_url' => 'mysql://wiki_user:super-secret-password@localhost:3306/wiki_engine',
    'mariadb_password' => 'super-secret-password',
]);
$exportCollector = new OperationalDiagnosticsCollector(
    $connectedWithSchemaPdo,
    'connected',
    $exportConfigLoader,
    new StoragePathConfig(new ConfigLoader([]), $storageRoot),
    '1.2.3'
);
$exportSnapshot = $exportCollector->collectExportSnapshot();

foreach ($exportSnapshot as $key => $value) {
    if (!is_string($value)) {
        $failures[] = "(7) export 스냅샷의 모든 값은 문자열이어야 한다 (key={$key}).";
    }
}

$exportJson = json_encode($exportSnapshot, JSON_THROW_ON_ERROR);
if (str_contains($exportJson, 'super-secret-password')) {
    $failures[] = '(7) export 스냅샷이 DB 비밀번호를 담으면 안 된다.';
}
if (!isset($exportSnapshot['db_status'], $exportSnapshot['schema_status'], $exportSnapshot['cache_status'], $exportSnapshot['app_version'])) {
    $failures[] = '(7) export 스냅샷이 db_status/schema_status/cache_status/app_version 항목을 포함해야 한다.';
}

@rmdir($cacheDir);
@rmdir($storageRoot);

if ($failures !== []) {
    fwrite(STDERR, "OperationalDiagnosticsCollector 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "OperationalDiagnosticsCollector 테스트 통과.\n");
exit(0);
