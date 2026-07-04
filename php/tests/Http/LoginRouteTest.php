<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0686에서 등록하는 `GET`/`POST /login`,
 * `GET`/`POST /logout` route의 동작을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다(0685 DocumentEditRouteTest.php와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직을 Router에
 * 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 로그인하지 않은 상태에서 GET /login은 200으로 로그인 폼(CSRF 토큰
 *     포함)을 렌더링한다.
 * (2) 잘못된 CSRF 토큰으로 POST /login하면 403을 반환하고 세션에 로그인
 *     상태가 남지 않는다.
 * (3) 올바른 CSRF 토큰이지만 틀린 자격 증명으로 POST /login하면 401을
 *     반환하고 세션에 로그인 상태가 남지 않는다.
 * (4) 올바른 자격 증명으로 POST /login하면 302로 "/"에 리다이렉트하고,
 *     세션에 계정 id가 저장된다.
 * (5) (4) 이후 같은 세션으로 GET /login에 접근하면(이미 로그인된 상태) 폼을
 *     다시 보여주지 않고 302로 "/"에 리다이렉트한다 — 세션에서 로그인
 *     상태가 실제로 복원됨을 보여준다.
 * (6) GET 또는 POST /logout하면 302로 "/"에 리다이렉트하고 세션을 비운다.
 * (7) (6) 로그아웃 이후 같은 세션으로 GET /login에 접근하면 다시 로그인
 *     폼을 200으로 보여준다(로그인 상태가 더 이상 복원되지 않는다).
 * (8) `$accountRepository`가 없으면(DB 미설정) GET /login은 로그인 여부를
 *     판단할 수 없으므로 항상 폼을 보여주고, POST /login은 503을 반환한다.
 * (9) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 `GET /login`이
 *     200(CSRF 토큰 포함)을 반환하고, 잘못된 CSRF 토큰의 `POST /login`은
 *     403을, `GET`/`POST /logout`은 302를 반환하며, 이어지는 `GET /health`도
 *     여전히 200을 반환하는지(프로세스가 죽지 않았다는 증거).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\AppBootstrap;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\LoginHandler;
use MintWiki\Security\LogoutHandler;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\LoginPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET/POST /login`, `GET/POST /logout` 핸들러와
 * 동일한 등록 로직을 재구성한다(위 파일 docblock 참고). index.php는 매
 * 요청마다 `new LoginHandler()`(기본 `AppBootstrap`)를 새로 만들지만, 이
 * 테스트에서는 실제 DB 없이 검증하기 위해 미리 구성한 `LoginHandler`를
 * 주입받는다.
 */
function mintwiki_register_login_routes(
    Router $router,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    LoginHandler $loginHandler
): void {
    $router->register('GET', '/login', static function () use ($accountRepository, $sessionAdapter): Response {
        if ($accountRepository !== null) {
            $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
            if ($currentUser !== null) {
                return new Response(302, ['Location' => '/']);
            }
        }

        $loginPage = new LoginPage();

        return Response::html($loginPage->render());
    });

    $router->register('POST', '/login', static function () use ($loginHandler): Response {
        return $loginHandler->handle($_POST);
    });

    $logoutRouteHandler = static function (): Response {
        $logoutHandler = new LogoutHandler();

        return $logoutHandler->handle();
    };
    $router->register('GET', '/logout', $logoutRouteHandler);
    $router->register('POST', '/logout', $logoutRouteHandler);
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
if ($accountSql === false) {
    fwrite(STDERR, "db/schema/account.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$createdConfigDirs = [];

function mintwiki_login_route_test_config_dir(): string
{
    global $createdConfigDirs;

    $dir = sys_get_temp_dir() . '/mintwiki_login_route_' . getmypid() . '_' . bin2hex(random_bytes(4));
    mkdir($dir, 0777, true);
    file_put_contents(
        $dir . '/local-config.php',
        "<?php\nreturn ['driver' => 'mysql', 'dsn' => 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4', 'user' => 'wiki_user', 'password' => 'sup3r-secret'];\n"
    );
    $createdConfigDirs[] = $dir;

    return $dir;
}

$plainPassword = 'correct horse battery staple';

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($accountSql);

$accountRepository = new AccountRepository($pdo);
$accountId = $accountRepository->create('admin', password_hash($plainPassword, PASSWORD_DEFAULT));

$sessionAdapter = new PhpSessionAdapter();
$csrfTokenService = new CsrfTokenService();
$bootstrap = new AppBootstrap(mintwiki_login_route_test_config_dir(), static fn (): PDO => $pdo);
$loginHandler = new LoginHandler($csrfTokenService, $bootstrap);

$router = new Router();
mintwiki_register_login_routes($router, $accountRepository, $sessionAdapter, $loginHandler);

try {
    // (1) 로그인하지 않은 상태에서 GET /login은 폼을 렌더링해야 한다.
    $_SESSION = [];

    $getLoginResponse = $router->match(new Request('GET', '/login'))();
    if ($getLoginResponse->status() !== 200) {
        $failures[] = '로그인하지 않은 상태의 GET /login은 200을 반환해야 하는데 ' . $getLoginResponse->status() . '이었다.';
    }
    if (!str_contains($getLoginResponse->body(), '<h1>로그인</h1>')) {
        $failures[] = 'GET /login은 로그인 폼을 보여줘야 한다.';
    }
    if (!preg_match('/name="csrf_token" value="[a-f0-9]{64}"/', $getLoginResponse->body())) {
        $failures[] = 'GET /login 응답은 CSRF 토큰 hidden input을 포함해야 한다.';
    }

    // (2) 잘못된 CSRF 토큰으로 POST /login하면 403이어야 한다.
    $_POST = ['csrf_token' => 'not-a-real-token', 'username' => 'admin', 'password' => $plainPassword];
    $badCsrfResponse = $router->match(new Request('POST', '/login'))();

    if ($badCsrfResponse->status() !== 403) {
        $failures[] = '잘못된 CSRF 토큰의 POST /login은 403을 반환해야 하는데 ' . $badCsrfResponse->status() . '이었다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = 'CSRF 검증 실패 시 세션에 로그인 상태가 남으면 안 된다.';
    }

    // (3) 올바른 CSRF지만 틀린 자격 증명이면 401이어야 한다.
    $validToken1 = $csrfTokenService->generate();
    $_POST = ['csrf_token' => $validToken1, 'username' => 'admin', 'password' => 'wrong-password'];
    $badCredentialsResponse = $router->match(new Request('POST', '/login'))();

    if ($badCredentialsResponse->status() !== 401) {
        $failures[] = '틀린 자격 증명의 POST /login은 401을 반환해야 하는데 ' . $badCredentialsResponse->status() . '이었다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = '자격 증명 실패 시 세션에 로그인 상태가 남으면 안 된다.';
    }

    // (4) 올바른 자격 증명이면 302로 "/"에 리다이렉트하고 세션에 계정 id가 저장되어야 한다.
    $validToken2 = $csrfTokenService->generate();
    $_POST = ['csrf_token' => $validToken2, 'username' => 'admin', 'password' => $plainPassword];
    $loginSuccessResponse = $router->match(new Request('POST', '/login'))();

    if ($loginSuccessResponse->status() !== 302) {
        $failures[] = '올바른 자격 증명의 POST /login은 302를 반환해야 하는데 ' . $loginSuccessResponse->status() . '이었다.';
    }
    if (($loginSuccessResponse->headers()['Location'] ?? null) !== '/') {
        $failures[] = '로그인 성공 시 Location은 "/"이어야 한다.';
    }
    if (($_SESSION[SessionUserResolver::SESSION_KEY] ?? null) !== $accountId) {
        $failures[] = '로그인 성공 이후 세션에 로그인한 계정 id가 저장되어야 한다.';
    }

    // (5) 로그인 상태에서 GET /login에 접근하면 폼 대신 302로 "/"에 리다이렉트해야
    // 한다 — 세션에서 로그인 상태가 실제로 복원됨을 보여준다.
    $alreadyLoggedInResponse = $router->match(new Request('GET', '/login'))();

    if ($alreadyLoggedInResponse->status() !== 302) {
        $failures[] = '이미 로그인된 상태의 GET /login은 302를 반환해야 하는데 ' . $alreadyLoggedInResponse->status() . '이었다.';
    }
    if (($alreadyLoggedInResponse->headers()['Location'] ?? null) !== '/') {
        $failures[] = '이미 로그인된 상태의 GET /login은 "/"로 리다이렉트해야 한다.';
    }

    // (6) GET 또는 POST /logout하면 302로 "/"에 리다이렉트하고 세션을 비워야 한다.
    $getLogoutResponse = $router->match(new Request('GET', '/logout'))();
    if ($getLogoutResponse->status() !== 302 || ($getLogoutResponse->headers()['Location'] ?? null) !== '/') {
        $failures[] = 'GET /logout은 302로 "/"에 리다이렉트해야 한다.';
    }
    if ($_SESSION !== []) {
        $failures[] = 'GET /logout 이후 세션이 완전히 비워져야 한다.';
    }

    // (7) 로그아웃 이후 같은 세션으로 GET /login에 접근하면 다시 로그인 폼을 보여줘야 한다.
    $afterLogoutLoginResponse = $router->match(new Request('GET', '/login'))();
    if ($afterLogoutLoginResponse->status() !== 200) {
        $failures[] = '로그아웃 이후 GET /login은 200을 반환해야 하는데 ' . $afterLogoutLoginResponse->status() . '이었다.';
    }
    if (!str_contains($afterLogoutLoginResponse->body(), '<h1>로그인</h1>')) {
        $failures[] = '로그아웃 이후 GET /login은 로그인 폼을 다시 보여줘야 한다.';
    }

    // POST /logout도 동일하게 동작해야 한다.
    $_SESSION = [SessionUserResolver::SESSION_KEY => $accountId];
    $postLogoutResponse = $router->match(new Request('POST', '/logout'))();
    if ($postLogoutResponse->status() !== 302 || ($postLogoutResponse->headers()['Location'] ?? null) !== '/') {
        $failures[] = 'POST /logout은 302로 "/"에 리다이렉트해야 한다.';
    }
    if ($_SESSION !== []) {
        $failures[] = 'POST /logout 이후 세션이 완전히 비워져야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(7) in-process 테스트 실패: ' . $e->getMessage();
}

// (8) $accountRepository가 없으면(DB 미설정) GET /login은 항상 폼을, POST /login은
// 503을 반환해야 한다.
try {
    $_SESSION = [];
    $unconfiguredBootstrap = new AppBootstrap(sys_get_temp_dir() . '/mintwiki_login_route_missing_config_' . getmypid());
    $unconfiguredLoginHandler = new LoginHandler(new CsrfTokenService(), $unconfiguredBootstrap);

    $unconfiguredRouter = new Router();
    mintwiki_register_login_routes($unconfiguredRouter, null, new PhpSessionAdapter(), $unconfiguredLoginHandler);

    $unconfiguredGetResponse = $unconfiguredRouter->match(new Request('GET', '/login'))();
    if ($unconfiguredGetResponse->status() !== 200) {
        $failures[] = 'DB 미설정 상태의 GET /login은 200을 반환해야 하는데 ' . $unconfiguredGetResponse->status() . '이었다.';
    }

    $_POST = ['csrf_token' => 'irrelevant', 'username' => 'admin', 'password' => $plainPassword];
    $unconfiguredPostResponse = $unconfiguredRouter->match(new Request('POST', '/login'))();
    if ($unconfiguredPostResponse->status() !== 403) {
        $failures[] = 'DB 미설정 상태에서 잘못된 CSRF 토큰의 POST /login은 403을 반환해야 하는데 ' . $unconfiguredPostResponse->status() . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(8) DB 미설정 테스트 실패: ' . $e->getMessage();
}

foreach ($createdConfigDirs as $dir) {
    @unlink($dir . '/local-config.php');
    @rmdir($dir);
}

// (9) DB 미설정 상태로 실제 index.php를 띄워도 라우팅이 동일하게 동작해야 한다.
const LOGIN_ROUTE_DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_login_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_login_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_login_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

/**
 * @return array{0: int, 1: string}
 */
function mintwiki_login_route_http_post(int $port, string $path, array $fields): array
{
    $body = http_build_query($fields);
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => $body,
            'ignore_errors' => true,
            'timeout' => 5,
        ],
    ]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

try {
    foreach (LOGIN_ROUTE_DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';

    $port = mintwiki_login_route_free_port();
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
        mintwiki_login_route_wait_for_server($port);

        [$getLoginStatus, $getLoginBody] = mintwiki_login_route_http_get($port, '/login');
        if ($getLoginStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /login은 200을 반환해야 하는데 ' . $getLoginStatus . '이었다.';
        }
        if (!str_contains($getLoginBody, 'name="csrf_token"')) {
            $failures[] = 'DB 미설정 상태에서 GET /login 응답은 CSRF 토큰 필드를 포함해야 한다.';
        }

        [$postLoginStatus] = mintwiki_login_route_http_post($port, '/login', [
            'csrf_token' => 'not-a-real-token',
            'username' => 'admin',
            'password' => 'irrelevant',
        ]);
        if ($postLoginStatus !== 403) {
            $failures[] = 'DB 미설정 상태에서 잘못된 CSRF 토큰의 POST /login은 403을 반환해야 하는데 ' . $postLoginStatus . '이었다.';
        }

        [$getLogoutStatus] = mintwiki_login_route_http_get($port, '/logout');
        if ($getLogoutStatus !== 302) {
            $failures[] = 'GET /logout은 302를 반환해야 하는데 ' . $getLogoutStatus . '이었다.';
        }

        [$postLogoutStatus] = mintwiki_login_route_http_post($port, '/logout', []);
        if ($postLogoutStatus !== 302) {
            $failures[] = 'POST /logout은 302를 반환해야 하는데 ' . $postLogoutStatus . '이었다.';
        }

        [$healthStatus] = mintwiki_login_route_http_get($port, '/health');
        if ($healthStatus !== 200) {
            $failures[] = '/login, /logout 요청 이후에도 GET /health는 200을 반환해야 하는데 ' . $healthStatus . '이었다(프로세스가 죽지 않았어야 한다).';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (LOGIN_ROUTE_DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(9) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /login, /logout route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /login, /logout route 테스트 통과.\n");
exit(0);
