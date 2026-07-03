<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\FlashMessageDisplay`의 동작을 확인하는 smoke test (태스크 0543).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 플래시 메시지가 올바르게 렌더링되는지,
 * 메시지 타입에 따라 다른 class가 적용되는지, XSS가 방지되는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\FlashMessageDisplay;
use MintWiki\Ui\FlashMessage;
use MintWiki\Ui\Escaper;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// (1) 메시지가 없을 때 빈 문자열 반환
$display = new FlashMessageDisplay();
$html = $display->render();

if ($html !== '') {
    $failures[] = '메시지가 없을 때 빈 문자열을 반환해야 한다.';
}

// (2) success 메시지 렌더링
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('저장되었습니다', 'success');

$escaper = new Escaper();
$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (!str_contains($html, '<div class="flash-message flash-message--success"')) {
    $failures[] = 'success 메시지가 올바른 class를 포함해야 한다.';
}

if (!str_contains($html, '저장되었습니다')) {
    $failures[] = '메시지 텍스트가 포함되어야 한다.';
}

if (!str_contains($html, '<p>저장되었습니다</p>')) {
    $failures[] = '메시지가 <p> 태그로 감싸져 있어야 한다.';
}

if (!str_contains($html, 'role="status"')) {
    $failures[] = '메시지가 role="status"를 포함해야 한다.';
}

if (!str_contains($html, 'aria-label="알림"')) {
    $failures[] = '메시지가 aria-label="알림"를 포함해야 한다.';
}

// (3) warning 메시지 렌더링
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('경고', 'warning');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (!str_contains($html, 'flash-message--warning')) {
    $failures[] = 'warning 메시지가 올바른 class를 포함해야 한다.';
}

// (4) error 메시지 렌더링
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('오류가 발생했습니다', 'error');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (!str_contains($html, 'flash-message--error')) {
    $failures[] = 'error 메시지가 올바른 class를 포함해야 한다.';
}

// (5) info 메시지 렌더링
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('정보 메시지', 'info');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (!str_contains($html, 'flash-message--info')) {
    $failures[] = 'info 메시지가 올바른 class를 포함해야 한다.';
}

// (6) XSS 공격으로부터 보호 - 메시지 escape
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('<script>alert("xss")</script>', 'success');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (str_contains($html, '<script>alert')) {
    $failures[] = 'script 태그가 escape되어야 한다.';
}

if (!str_contains($html, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')) {
    $failures[] = 'XSS 메시지가 올바르게 escape되어야 한다.';
}

// (7) HTML 특수 문자 escape
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('메시지 & < > " \'', 'success');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$html = $display->render();

if (!str_contains($html, '메시지 &amp; &lt; &gt; &quot; &#039;')) {
    $failures[] = '특수 문자들이 올바르게 escape되어야 한다.';
}

// (8) 닫음 div 태그 확인
if (!str_contains($html, '</div>')) {
    $failures[] = 'div 닫음 태그를 포함해야 한다.';
}

// (9) 기본 Escaper 사용
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('<script>test</script>', 'success');

$display = new FlashMessageDisplay();
$html = $display->render();

if (str_contains($html, '<script>')) {
    $failures[] = '기본 Escaper를 사용할 때도 script 태그가 escape되어야 한다.';
}

// (10) 메시지는 render() 후에 제거됨
$_SESSION = [];
$flashMessage = new FlashMessage();
$flashMessage->set('일회성 메시지', 'success');

$display = new FlashMessageDisplay($escaper, $flashMessage);
$firstRender = $display->render();
$secondRender = $display->render();

if (empty($firstRender)) {
    $failures[] = '첫 번째 render()에서 메시지를 포함해야 한다.';
}

if (!empty($secondRender)) {
    $failures[] = '두 번째 render()에서는 빈 문자열을 반환해야 한다 (메시지가 제거되어야 한다).';
}

if ($failures !== []) {
    fwrite(STDERR, "FlashMessageDisplay 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FlashMessageDisplay 테스트 통과.\n");
exit(0);
