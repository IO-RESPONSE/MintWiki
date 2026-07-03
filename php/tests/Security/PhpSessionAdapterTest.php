<?php

declare(strict_types=1);

/**
 * `MintWiki\Security\PhpSessionAdapter`의 skeleton 동작을 확인하는 smoke test.
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 실제 로그인 구현은 후속 태스크의
 * 범위이며, 여기서는 로그인 단계에서 사용할 세션 입출력 경계만 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\PhpSessionAdapter;

$failures = [];
$adapter = new PhpSessionAdapter();

// (1) 세션 시작
$adapter->start();
$_SESSION = [];

if (!$adapter->isStarted()) {
    $failures[] = 'start()는 PHP 세션을 활성 상태로 만들어야 한다.';
}

// (2) 로그인 단계에서 사용할 사용자 식별자 저장/조회
$adapter->set('user_id', 'user-123');

if ($adapter->get('user_id') !== 'user-123') {
    $failures[] = 'set()으로 저장한 로그인 사용자 식별자를 get()으로 읽을 수 있어야 한다.';
}

// (3) 배열 값 저장/조회
$adapter->set('auth_context', [
    'username' => 'admin',
    'roles' => ['admin'],
]);

$authContext = $adapter->get('auth_context');

if (!is_array($authContext) || $authContext['username'] !== 'admin' || $authContext['roles'] !== ['admin']) {
    $failures[] = '배열 형태의 인증 context를 세션에 저장하고 읽을 수 있어야 한다.';
}

// (4) 기본값 반환
if ($adapter->get('missing_key', 'fallback') !== 'fallback') {
    $failures[] = 'get()은 키가 없을 때 지정한 기본값을 반환해야 한다.';
}

// (5) 값 제거
$adapter->remove('user_id');

if ($adapter->get('user_id') !== null) {
    $failures[] = 'remove()는 지정한 세션 키를 제거해야 한다.';
}

// (6) 전체 값 비우기
$adapter->set('csrf_tokens', ['token' => true]);
$adapter->set('flash_message', ['message' => '저장됨', 'type' => 'success']);
$adapter->clear();

if ($_SESSION !== []) {
    $failures[] = 'clear()는 현재 세션 값을 모두 비워야 한다.';
}

// (7) 로그인 성공 시 세션 ID 재발급 진입점
$adapter->set('user_id', 'user-456');
$beforeId = session_id();
$regenerated = $adapter->regenerateId();
$afterId = session_id();

if (!$regenerated) {
    $failures[] = 'regenerateId()는 세션 ID 재발급 성공 여부를 true로 반환해야 한다.';
}

if ($beforeId === '' || $afterId === '') {
    $failures[] = 'regenerateId() 전후에는 세션 ID가 비어 있지 않아야 한다.';
}

if ($adapter->get('user_id') !== 'user-456') {
    $failures[] = 'regenerateId()는 기존 로그인 세션 값을 유지해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "PhpSessionAdapter 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PhpSessionAdapter 테스트 통과.\n");
exit(0);
