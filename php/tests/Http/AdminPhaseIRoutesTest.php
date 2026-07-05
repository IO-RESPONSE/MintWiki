<?php

declare(strict_types=1);

/**
 * 0700-0702 관리자 콘솔 Phase I 라우트 wiring smoke test.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\Effect;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission;
use MintWiki\Acl\SubjectType;
use MintWiki\Admin\BackupRunner;
use MintWiki\App\MaintenanceModeStateStore;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\BackupPage;
use MintWiki\Ui\FilePermissionDiagnosticsPage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\MaintenanceModePage;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\NavigationItem;
use MintWiki\Ui\OperationalDiagnosticsPage;
use MintWiki\Ui\RestorePage;
use MintWiki\User\AccountRepository;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

final class AdminPhaseITestBackupRunner implements BackupRunner
{
    public int $createCount = 0;
    public int $restoreCount = 0;

    public function createBackup(): string
    {
        $this->createCount++;

        return 'test-backup.json';
    }

    public function listBackups(): array
    {
        return $this->createCount > 0 ? ['test-backup.json'] : [];
    }

    public function restoreBackup(array $uploadedFile): string
    {
        $this->restoreCount++;

        if (($uploadedFile['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
            throw new RuntimeException('복원할 백업 파일을 선택하세요.');
        }

        return 'restored.json';
    }
}

function admin_phase_i_layout(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter, AclService $aclService, string $path): Layout
{
    $currentUser = $accountRepository !== null
        ? (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve()
        : null;
    $items = [new NavigationItem('/write', '글쓰기', '/write')];
    if ($currentUser !== null && $aclService->check(Permission::Admin, SubjectType::User, $currentUser->id())->isAllowed()) {
        $items[] = new NavigationItem('/admin', '관리', '/admin');
    }

    return new Layout(null, (new NavigationBar())->render(new Navigation($items), $path, [], $currentUser));
}

function admin_phase_i_authorize(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter, AclService $aclService, Layout $layout): ?Response
{
    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    return (new AdminAccessGate($aclService, new SessionUserResolver($sessionAdapter, $accountRepository), $layout))->authorize();
}

function admin_phase_i_register_routes(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService,
    MaintenanceModeStateStore $maintenanceStore,
    BackupRunner $backupRunner
): void {
    $router->register('GET', '/admin/maintenance', static function () use ($accountRepository, $sessionAdapter, $aclService, $maintenanceStore): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/maintenance');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }

        return Response::html((new MaintenanceModePage(null, $layout))->renderAdmin($maintenanceStore->isEnabled()));
    });

    $router->register('POST', '/admin/maintenance', static function () use ($accountRepository, $sessionAdapter, $aclService, $maintenanceStore): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/maintenance');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }
        $page = new MaintenanceModePage(null, $layout);
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
        if (!(new CsrfTokenService())->validate($csrfToken)) {
            return Response::html($page->renderAdmin($maintenanceStore->isEnabled(), ['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.']), 403);
        }
        $maintenanceStore->setEnabled(($_POST['enabled'] ?? null) === '1');

        return new Response(302, ['Location' => '/admin/maintenance']);
    });

    $router->register('GET', '/admin/backup', static function () use ($accountRepository, $sessionAdapter, $aclService, $backupRunner): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/backup');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }

        return Response::html((new BackupPage(null, $layout))->render($backupRunner->listBackups()));
    });

    $router->register('POST', '/admin/backup', static function () use ($accountRepository, $sessionAdapter, $aclService, $backupRunner): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/backup');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }
        $page = new BackupPage(null, $layout);
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
        if (!(new CsrfTokenService())->validate($csrfToken)) {
            return Response::html($page->render($backupRunner->listBackups(), null, ['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.']), 403);
        }

        return Response::html($page->render($backupRunner->listBackups(), '백업을 생성했습니다: ' . $backupRunner->createBackup()));
    });

    $router->register('GET', '/admin/restore', static function () use ($accountRepository, $sessionAdapter, $aclService): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/restore');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }

        return Response::html((new RestorePage(null, $layout))->render());
    });

    $router->register('POST', '/admin/restore', static function () use ($accountRepository, $sessionAdapter, $aclService, $backupRunner): Response {
        $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/admin/restore');
        $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
        if ($gate !== null) {
            return $gate;
        }
        $page = new RestorePage(null, $layout);
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
        if (!(new CsrfTokenService())->validate($csrfToken)) {
            return Response::html($page->render(['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.']), 403);
        }
        if (($_POST['confirm_restore'] ?? null) !== '1') {
            return Response::html($page->render(['confirm_restore' => '복원을 실행하려면 위험 작업 확인에 동의해야 합니다.']), 422);
        }
        $backupRunner->restoreBackup(is_array($_FILES['backup_file'] ?? null) ? $_FILES['backup_file'] : []);

        return new Response(302, ['Location' => '/admin/backup']);
    });

    foreach ([
        '/admin/diagnostics' => static fn (Layout $layout): string => (new OperationalDiagnosticsPage(null, $layout))->render(),
        '/admin/diagnostics/files' => static fn (Layout $layout): string => (new FilePermissionDiagnosticsPage(null, $layout))->render(),
    ] as $path => $renderer) {
        $router->register('GET', $path, static function () use ($accountRepository, $sessionAdapter, $aclService, $path, $renderer): Response {
            $layout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, $path);
            $gate = admin_phase_i_authorize($accountRepository, $sessionAdapter, $aclService, $layout);
            if ($gate !== null) {
                return $gate;
            }

            return Response::html($renderer($layout));
        });
    }
}

$failures = [];

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
if ($accountSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "필수 schema fixture를 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($accountSql);
$pdo->exec($aclNamespaceRuleSql);
$accountRepository = new AccountRepository($pdo);
$adminId = $accountRepository->create('admin', password_hash('irrelevant', PASSWORD_DEFAULT));
$regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));

$aclRepository = new AclPdoRepository($pdo);
$aclRepository->grantNamespacePermission(NamespaceAclDefaults::DEFAULT_NAMESPACE, SubjectType::User, Permission::Admin, Effect::Allow, $adminId);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, $aclRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE));
$aclService = new AclService($namespaceAclDefaults);

$sessionAdapter = new PhpSessionAdapter();
$stateFile = sys_get_temp_dir() . '/mintwiki-maintenance-' . getmypid() . '.php';
@unlink($stateFile);
$maintenanceStore = new MaintenanceModeStateStore($stateFile);
$backupRunner = new AdminPhaseITestBackupRunner();
$router = new Router();
admin_phase_i_register_routes($router, $accountRepository, $sessionAdapter, $aclService, $maintenanceStore, $backupRunner);

$_SESSION = [];
$anonDiagnostics = $router->match(new Request('GET', '/admin/diagnostics'))();
if ($anonDiagnostics->status() !== 302 || ($anonDiagnostics->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '익명 GET /admin/diagnostics는 /login 302여야 한다.';
}

$_SESSION = [SessionUserResolver::SESSION_KEY => $regularId];
$regularDiagnostics = $router->match(new Request('GET', '/admin/diagnostics'))();
if ($regularDiagnostics->status() !== 403) {
    $failures[] = '비관리자 GET /admin/diagnostics는 403이어야 한다.';
}
$regularHomeLayout = admin_phase_i_layout($accountRepository, $sessionAdapter, $aclService, '/');
if (str_contains($regularHomeLayout->render('x', '<main></main>'), 'href="/admin"')) {
    $failures[] = '비관리자 상단바에는 관리 링크가 없어야 한다.';
}

$_SESSION = [SessionUserResolver::SESSION_KEY => $adminId];
$adminDiagnostics = $router->match(new Request('GET', '/admin/diagnostics'))();
if ($adminDiagnostics->status() !== 200 || !str_contains($adminDiagnostics->body(), '<h1>운영 진단</h1>')) {
    $failures[] = '관리자 GET /admin/diagnostics는 운영 진단 page를 반환해야 한다.';
}
if (!str_contains($adminDiagnostics->body(), 'href="/admin"') || !str_contains($adminDiagnostics->body(), '>관리<')) {
    $failures[] = '관리자 상단바에는 관리 링크가 노출되어야 한다.';
}

$fileDiagnostics = $router->match(new Request('GET', '/admin/diagnostics/files'))();
if ($fileDiagnostics->status() !== 200 || !str_contains($fileDiagnostics->body(), '<h1>파일 권한 진단</h1>')) {
    $failures[] = '관리자 GET /admin/diagnostics/files는 파일 권한 진단 page를 반환해야 한다.';
}

$maintenanceGet = $router->match(new Request('GET', '/admin/maintenance'))();
if ($maintenanceGet->status() !== 200 || !str_contains($maintenanceGet->body(), 'action="/admin/maintenance"')) {
    $failures[] = '관리자 GET /admin/maintenance는 토글 폼을 반환해야 한다.';
}

$_POST = ['csrf_token' => 'bad', 'enabled' => '1'];
$maintenanceBadCsrf = $router->match(new Request('POST', '/admin/maintenance'))();
if ($maintenanceBadCsrf->status() !== 403 || $maintenanceStore->isEnabled()) {
    $failures[] = '유지보수 POST는 잘못된 CSRF를 403으로 거부하고 상태를 바꾸지 않아야 한다.';
}

$token = (new CsrfTokenService())->generate();
$_POST = ['csrf_token' => $token, 'enabled' => '1'];
$maintenancePost = $router->match(new Request('POST', '/admin/maintenance'))();
if ($maintenancePost->status() !== 302 || !$maintenanceStore->isEnabled()) {
    $failures[] = '유효한 유지보수 POST는 상태를 저장하고 302를 반환해야 한다.';
}

$shouldBlockHome = $maintenanceStore->isEnabled()
    && '/' !== '/login'
    && '/' !== '/health'
    && !str_starts_with('/', '/admin');
if (!$shouldBlockHome) {
    $failures[] = '유지보수 ON이면 일반 요청은 차단 대상이어야 한다.';
}
foreach (['/login', '/health', '/admin/maintenance'] as $path) {
    $allowedDuringMaintenance = $path === '/login' || $path === '/health' || str_starts_with($path, '/admin');
    if (!$allowedDuringMaintenance) {
        $failures[] = "유지보수 예외 경로 판정 실패: {$path}";
    }
}

$_POST = ['csrf_token' => 'bad'];
$backupBadCsrf = $router->match(new Request('POST', '/admin/backup'))();
if ($backupBadCsrf->status() !== 403 || $backupRunner->createCount !== 0) {
    $failures[] = '백업 POST는 잘못된 CSRF를 거부하고 실행기를 호출하지 않아야 한다.';
}

$token = (new CsrfTokenService())->generate();
$_POST = ['csrf_token' => $token];
$backupPost = $router->match(new Request('POST', '/admin/backup'))();
if ($backupPost->status() !== 200 || $backupRunner->createCount !== 1 || !str_contains($backupPost->body(), '백업을 생성했습니다')) {
    $failures[] = '유효한 백업 POST는 백업 실행기를 호출하고 결과를 표시해야 한다.';
}

$token = (new CsrfTokenService())->generate();
$_POST = ['csrf_token' => $token];
$_FILES = [];
$restoreMissingConfirm = $router->match(new Request('POST', '/admin/restore'))();
if ($restoreMissingConfirm->status() !== 422 || $backupRunner->restoreCount !== 0) {
    $failures[] = '복원 POST는 위험 확인이 없으면 422로 거부해야 한다.';
}

$token = (new CsrfTokenService())->generate();
$_POST = ['csrf_token' => $token, 'confirm_restore' => '1'];
$_FILES = ['backup_file' => ['name' => 'backup.json', 'tmp_name' => __FILE__, 'error' => UPLOAD_ERR_OK]];
$restorePost = $router->match(new Request('POST', '/admin/restore'))();
if ($restorePost->status() !== 302 || $backupRunner->restoreCount !== 1) {
    $failures[] = '유효한 복원 POST는 실행기를 호출하고 /admin/backup으로 302해야 한다.';
}

@unlink($stateFile);

if ($failures !== []) {
    fwrite(STDERR, "관리자 콘솔 Phase I route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "관리자 콘솔 Phase I route 테스트 통과.\n");
exit(0);
