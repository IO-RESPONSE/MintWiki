<?php

declare(strict_types=1);

/**
 * Phase K(태스크 0714-0717: 감사 기록 배선, 문서 삭제, 백업 직접 다운로드,
 * 운영 진단 실데이터+export)가 실제 배포 Ui 컴포넌트/도메인 모듈에 빠짐없이
 * 통합되어 있는지 확인하는 연기 테스트(태스크 0718). phpunit 없이 `php`
 * CLI만으로 실행되며, DB/자격 증명 없이 항상 실행할 수 있다(0713
 * `UiPhaseJSmokeTest.php`와 동일한 방식) — 개별 기능 단위 테스트
 * (DocumentDeleteRouteTest.php, PdoAuditRecorderTest.php,
 * BackupDownloadRouteTest.php, DiagnosticsExportRouteTest.php 등)와 달리,
 * 네 기능이 배포되는 Ui 컴포넌트/도메인 모듈과 함께 실제로 맞물리는지를
 * 한 번에 확인한다.
 *
 * 확인 대상(0718 acceptance criteria):
 * (1) 문서 삭제: 확인 화면이 위험 작업 체크박스/CSRF 토큰을 갖췄는지.
 * (2) 감사 로그: 실제 감사 이벤트가 빈 상태 대신 표로 렌더링되는지.
 * (3) 백업 다운로드: 백업 목록에 다운로드 링크가 걸리고, traversal/목록에
 *     없는 파일명은 `FileBackupRunner::resolveBackupPath()`가 거부하는지.
 * (4) 운영 진단: DB/스키마/캐시/환경 실데이터가 렌더링되고, 민감 key는
 *     export 스냅샷에서 제외되는지.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Admin\FileBackupRunner;
use MintWiki\App\ConfigLoader;
use MintWiki\App\OperationalDiagnosticsCollector;
use MintWiki\App\SensitiveDiagnosticsFilter;
use MintWiki\App\StoragePathConfig;
use MintWiki\Audit\AuditEventRecord;
use MintWiki\Ui\AuditViewerPage;
use MintWiki\Ui\BackupPage;
use MintWiki\Ui\DocumentDeletePage;
use MintWiki\Ui\OperationalDiagnosticsPage;

$failures = [];

// ============================================================================
// (1) 문서 삭제 확인 화면: 위험 작업 체크박스 + CSRF 토큰 + 취소 링크.
// ============================================================================

$deletePage = new DocumentDeletePage();
$deleteBody = $deletePage->render('Phase K Smoke Test Document');

if (!str_contains($deleteBody, 'name="confirm_delete"')) {
    $failures[] = '문서 삭제 확인 화면이 위험 작업 확인 체크박스(confirm_delete)를 포함해야 한다(태스크 0715).';
}
if (!str_contains($deleteBody, 'name="csrf_token"')) {
    $failures[] = '문서 삭제 확인 화면이 CSRF 토큰을 포함해야 한다(태스크 0715).';
}
if (!str_contains($deleteBody, 'action="/wiki/' . rawurlencode('Phase K Smoke Test Document') . '/delete"')) {
    $failures[] = '문서 삭제 확인 화면의 form이 /wiki/{title}/delete로 제출되어야 한다(태스크 0715).';
}

// ============================================================================
// (2) 감사 로그: 실제 이벤트가 빈 상태 대신 표로 렌더링되어야 한다.
// ============================================================================

$auditEvents = [
    new AuditEventRecord(
        'evt-1',
        'document',
        'deleted',
        'doc-phase-k',
        null,
        'smoke-admin',
        '2026-07-06 09:00:00'
    ),
    new AuditEventRecord(
        'evt-2',
        'backup',
        'downloaded',
        'mintwiki-backup-20260706-090000.json',
        null,
        null,
        '2026-07-06 09:05:00'
    ),
];

$auditBody = (new AuditViewerPage())->render($auditEvents);

if (str_contains($auditBody, '감사 로그가 없습니다')) {
    $failures[] = '감사 이벤트가 있으면 빈 상태 메시지를 보여주면 안 된다(태스크 0714, 0698).';
}
if (!str_contains($auditBody, 'document.deleted')) {
    $failures[] = '감사 로그 표가 실제 이벤트(module.action)를 렌더링해야 한다(태스크 0714).';
}
if (!str_contains($auditBody, 'smoke-admin')) {
    $failures[] = '감사 로그 표가 실제 행위자(actor_id)를 렌더링해야 한다(태스크 0714).';
}
if (!str_contains($auditBody, '시스템')) {
    $failures[] = '행위자가 없는(시스템) 이벤트도 표에서 누락되지 않아야 한다(태스크 0714).';
}

// ============================================================================
// (3) 백업 다운로드: 목록에 다운로드 링크, traversal/미등록 파일명은 거부.
// ============================================================================

$backupDirectory = sys_get_temp_dir() . '/mintwiki-phase-k-smoke-' . bin2hex(random_bytes(4));
$backupRunner = new FileBackupRunner($backupDirectory);
$backupName = $backupRunner->createBackup();

$backupBody = (new BackupPage())->render($backupRunner->listBackups());

if (!str_contains($backupBody, '/admin/backup/download/' . rawurlencode($backupName))) {
    $failures[] = '백업 목록 화면이 실제 백업 파일의 다운로드 링크를 렌더링해야 한다(태스크 0716).';
}

if ($backupRunner->resolveBackupPath('../outside.json') !== null) {
    $failures[] = 'resolveBackupPath()가 경로 traversal 파일명을 거부해야 한다(태스크 0716).';
}
if ($backupRunner->resolveBackupPath('not-a-real-backup.json') !== null) {
    $failures[] = 'resolveBackupPath()가 목록에 없는 파일명을 거부해야 한다(태스크 0716).';
}

// 임시 백업 디렉터리를 정리한다 — smoke test가 저장소에 잔여 파일을 남기지 않는다.
foreach ($backupRunner->listBackups() as $leftoverBackup) {
    @unlink($backupDirectory . '/' . $leftoverBackup);
}
@rmdir($backupDirectory);

// ============================================================================
// (4) 운영 진단: DB/스키마/캐시/환경 실데이터 렌더링 + 민감 key export 제외.
// ============================================================================

$storagePathConfig = new StoragePathConfig(new ConfigLoader());
$diagnosticsCollector = new OperationalDiagnosticsCollector(
    null,
    'unconfigured',
    new ConfigLoader(),
    $storagePathConfig,
    '0.0.0-smoke'
);

$diagnosticsBody = (new OperationalDiagnosticsPage())->render($diagnosticsCollector->collect());

if (!str_contains($diagnosticsBody, 'aria-label="데이터베이스 상태"')) {
    $failures[] = '운영 진단 화면이 데이터베이스 상태 섹션을 렌더링해야 한다(태스크 0717).';
}
if (!str_contains($diagnosticsBody, 'aria-label="스키마 상태"')) {
    $failures[] = '운영 진단 화면이 스키마 상태 섹션을 렌더링해야 한다(태스크 0717).';
}
if (!str_contains($diagnosticsBody, 'aria-label="캐시 상태"')) {
    $failures[] = '운영 진단 화면이 캐시 상태 섹션을 렌더링해야 한다(태스크 0717).';
}
if (!str_contains($diagnosticsBody, '/admin/diagnostics/export')) {
    $failures[] = '운영 진단 화면이 환경 진단 export 다운로드 링크를 포함해야 한다(태스크 0717).';
}

$exportSnapshot = $diagnosticsCollector->collectExportSnapshot();
$exportSnapshotWithSecret = $exportSnapshot + ['db_password' => 'hunter2', 'database_url' => 'mysql://user:hunter2@host/db'];
$filteredSnapshot = SensitiveDiagnosticsFilter::filter($exportSnapshotWithSecret);

if (array_key_exists('db_password', $filteredSnapshot) || array_key_exists('database_url', $filteredSnapshot)) {
    $failures[] = 'export 스냅샷 필터가 password/DSN 계열 key를 제외해야 한다(태스크 0717).';
}
if (str_contains(json_encode($filteredSnapshot, JSON_THROW_ON_ERROR), 'hunter2')) {
    $failures[] = 'export 스냅샷에는 어떤 형태로도 비밀번호 값이 남아있으면 안 된다(태스크 0717).';
}

if ($failures !== []) {
    fwrite(STDERR, "Phase K 통합 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Phase K 통합 연기 테스트 통과.\n");
exit(0);
