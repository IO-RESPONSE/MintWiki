<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\FlashMessage`의 동작을 확인하는 smoke test (태스크 0543).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 플래시 메시지가 올바르게
 * 저장되고 검색되는지, 그리고 검색 후 제거되는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\FlashMessage;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// (1) 메시지가 없을 때 null 반환
$flashMessage = new FlashMessage();
$result = $flashMessage->get();

if ($result !== null) {
    $failures[] = '메시지가 없을 때 null을 반환해야 한다.';
}

// (2) 메시지 저장
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('문서가 생성되었습니다');

$message = $flashMessage->get();

if ($message === null) {
    $failures[] = 'set()으로 저장한 메시지를 get()으로 검색해야 한다.';
}

if ($message['message'] !== '문서가 생성되었습니다') {
    $failures[] = 'get()은 저장된 메시지 텍스트를 반환해야 한다.';
}

if ($message['type'] !== 'success') {
    $failures[] = '기본 메시지 타입은 "success"여야 한다.';
}

// (3) 메시지 타입 지정
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('경고 메시지입니다', 'warning');

$message = $flashMessage->get();

if ($message['type'] !== 'warning') {
    $failures[] = 'set()으로 지정한 메시지 타입이 저장되어야 한다.';
}

// (4) 메시지는 한 번 검색되면 제거됨
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('일회성 메시지');

$firstGet = $flashMessage->get();
$secondGet = $flashMessage->get();

if ($firstGet === null) {
    $failures[] = '첫 번째 get()에서 메시지를 반환해야 한다.';
}

if ($secondGet !== null) {
    $failures[] = '두 번째 get()에서는 null을 반환해야 한다 (메시지가 제거되어야 한다).';
}

// (5) 다른 메시지 타입 저장
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('오류가 발생했습니다', 'error');

$message = $flashMessage->get();

if ($message['type'] !== 'error') {
    $failures[] = '"error" 타입 메시지를 저장 및 검색할 수 있어야 한다.';
}

// (6) info 타입 메시지
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('정보 메시지입니다', 'info');

$message = $flashMessage->get();

if ($message['type'] !== 'info') {
    $failures[] = '"info" 타입 메시지를 저장 및 검색할 수 있어야 한다.';
}

// (7) 특수 문자를 포함한 메시지
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('문서 "테스트" & 정보가 저장되었습니다');

$message = $flashMessage->get();

if ($message['message'] !== '문서 "테스트" & 정보가 저장되었습니다') {
    $failures[] = '특수 문자를 포함한 메시지를 저장 및 검색할 수 있어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "FlashMessage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FlashMessage 테스트 통과.\n");
exit(0);
