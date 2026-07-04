<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0677에서 등록하는 `GET /install`,
 * `GET /install/requirements` route 핸들러의 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(0526 HomePageRouteTest.php와 동일한
 * 방식) — index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직을
 * Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) GET /install이 `InstallWelcomePage`를 200으로 렌더하는지.
 * (2) GET /install/requirements가 `RequirementCheck`를 통과한 상태에서는
 *     추가 안내 없이 `InstallRequiredPage`의 기본 화면을 200으로 렌더하는지.
 * (3) `RequirementCheck`가 실패를 보고하면 그 결과가 실제로 화면에 반영되는지
 *     (index.php와 동일한 조합 로직을 재현해서 검증).
 * (4) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 두 route 모두
 *     200으로 응답하는지(InstallerRouteGateWiringTest.php (3)과 동일한 방식) —
 *     설치 완료 시 InstallerRouteGate가 두 route를 차단하는 것은 0676
 *     InstallerRouteGateWiringTest.php에서 `/install/step-1` sub-path로 이미
 *     검증되어 있다(같은 접두사 규칙을 `/install/requirements`에도 그대로 적용).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Installer\RequirementCheck;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallWelcomePage;

$failures = [];

$router = new Router();

$router->register('GET', '/install', static function (): Response {
    $installWelcomePage = new InstallWelcomePage();

    return Response::html($installWelcomePage->render());
});

$router->register('GET', '/install/requirements', static function (): Response {
    $requirementCheck = new RequirementCheck();
    $missingRequirements = [];

    try {
        $requirementCheck->areRequiredExtensionsLoaded();
    } catch (\RuntimeException $exception) {
        $missingRequirements[] = $exception->getMessage();
    }

    try {
        $requirementCheck->areRequiredDirectoriesWritable();
    } catch (\RuntimeException $exception) {
        $missingRequirements[] = $exception->getMessage();
    }

    $installRequiredPage = new InstallRequiredPage();

    return Response::html($installRequiredPage->render($missingRequirements));
});

// (1) GET /install이 InstallWelcomePage를 200으로 렌더해야 한다.
$installHandler = $router->match(new Request('GET', '/install'));
if ($installHandler === null) {
    $failures[] = 'GET /install route는 등록되어 있어야 한다.';
} else {
    $response = $installHandler();
    if ($response->status() !== 200) {
        $failures[] = 'GET /install 응답의 status는 200이어야 한다.';
    }
    $body = $response->body();
    if (!str_contains($body, '<h1>설치 환영</h1>')) {
        $failures[] = 'GET /install 응답이 설치 환영 page의 h1을 포함해야 한다.';
    }
    if (!str_contains($body, 'MintWiki 설치를 시작합니다.')) {
        $failures[] = 'GET /install 응답이 설치 환영 안내 문구를 포함해야 한다.';
    }
}

// (2) GET /install/requirements가 기본 환경(요구사항 충족)에서는 추가 안내
// 없이 InstallRequiredPage의 기본 화면을 200으로 렌더해야 한다. 이 CI 환경은
// pdo/json 확장이 있고 기본 필수 디렉터리 목록이 비어 있으므로 항상 통과한다.
$requirementsHandler = $router->match(new Request('GET', '/install/requirements'));
if ($requirementsHandler === null) {
    $failures[] = 'GET /install/requirements route는 등록되어 있어야 한다.';
} else {
    $response = $requirementsHandler();
    if ($response->status() !== 200) {
        $failures[] = 'GET /install/requirements 응답의 status는 200이어야 한다.';
    }
    $body = $response->body();
    if (!str_contains($body, '<h1>설치 필요</h1>')) {
        $failures[] = 'GET /install/requirements 응답이 InstallRequiredPage의 h1을 포함해야 한다.';
    }
    if (str_contains($body, '충족되지 않은 시스템 요구사항')) {
        $failures[] = '요구사항을 모두 충족한 환경에서는 누락 안내 목록이 나타나면 안 된다.';
    }
}

// (3) RequirementCheck가 실패를 보고하면(존재하지 않는 확장), 그 실패 메시지가
// InstallRequiredPage 화면에 반영되어야 한다 — index.php의 조합 로직을 그대로
// 재현해 검증한다.
$failingRequirementCheck = new RequirementCheck(['nonexistent_extension_xyz']);
$missingRequirements = [];
try {
    $failingRequirementCheck->areRequiredExtensionsLoaded();
} catch (\RuntimeException $exception) {
    $missingRequirements[] = $exception->getMessage();
}
try {
    $failingRequirementCheck->areRequiredDirectoriesWritable();
} catch (\RuntimeException $exception) {
    $missingRequirements[] = $exception->getMessage();
}

if ($missingRequirements === []) {
    $failures[] = '존재하지 않는 확장을 요구하면 누락 요구사항이 최소 1개 이상이어야 한다.';
} else {
    $installRequiredPage = new InstallRequiredPage();
    $html = $installRequiredPage->render($missingRequirements);

    if (!str_contains($html, '충족되지 않은 시스템 요구사항')) {
        $failures[] = 'RequirementCheck 실패 결과가 InstallRequiredPage 화면에 안내되어야 한다.';
    }
    if (!str_contains($html, 'nonexistent_extension_xyz')) {
        $failures[] = 'RequirementCheck 실패 결과에 누락된 확장 이름이 포함되어야 한다.';
    }
}

// 등록되지 않은 method/path는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('POST', '/install')) !== null) {
    $failures[] = 'POST /install는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/install/nonexistent')) !== null) {
    $failures[] = 'GET /install/nonexistent는 등록되어 있지 않으므로 null을 반환해야 한다.';
}

// (4) DB 미설정 상태로 실제 index.php를 띄워도 두 route가 200으로 응답해야
// 한다(InstallerRouteGateWiringTest.php (3)과 동일한 방식).
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_install_routes_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_install_routes_wait_for_server(int $port, float $timeout = 5.0): void
{
    $deadline = microtime(true) + $timeout;
    while (microtime(true) < $deadline) {
        $connection = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
        if ($connection !== false) {
            fclose($connection);

            return;
        }
        usleep(50000);
    }

    throw new RuntimeException("php -S 서버(포트 {$port})가 제한 시간 안에 준비되지 않았습니다.");
}

/**
 * @return array{0: int, 1: string}
 */
function mintwiki_install_routes_http_get(int $port, string $path): array
{
    $context = stream_context_create([
        'http' => ['method' => 'GET', 'ignore_errors' => true, 'timeout' => 5],
    ]);
    $body = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $body === false ? '' : $body];
}

try {
    foreach (DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';
    $port = mintwiki_install_routes_free_port();
    $process = proc_open(
        ['php', '-S', "127.0.0.1:{$port}", '-t', $publicDir],
        [1 => ['pipe', 'w'], 2 => ['pipe', 'w']],
        $pipes,
        $publicDir
    );

    if ($process === false) {
        throw new RuntimeException('php -S 서버를 시작하지 못했습니다.');
    }

    try {
        mintwiki_install_routes_wait_for_server($port);

        [$installStatus, $installBody] = mintwiki_install_routes_http_get($port, '/install');
        if ($installStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install은 200을 반환해야 한다.';
        }
        if (!str_contains($installBody, '<h1>설치 환영</h1>')) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install 응답이 설치 환영 화면이어야 한다.';
        }

        [$requirementsStatus, $requirementsBody] = mintwiki_install_routes_http_get($port, '/install/requirements');
        if ($requirementsStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install/requirements는 200을 반환해야 한다.';
        }
        if (!str_contains($requirementsBody, '<h1>설치 필요</h1>')) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install/requirements 응답이 요구사항 점검 화면이어야 한다.';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(4) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /install, GET /install/requirements route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /install, GET /install/requirements route 테스트 통과.\n");
exit(0);
