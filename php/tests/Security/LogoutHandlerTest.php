<?php

declare(strict_types=1);

/**
 * `MintWiki\Security\LogoutHandler`(`GET`/`POST /logout` 처리, 태스크 0686)의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 검증 대상:
 * (1) 로그인 상태(세션에 계정 id/기타 값 존재)에서 handle()을 호출하면
 *     세션이 완전히 비워지고 302로 홈("/")으로 리다이렉트된다.
 * (2) 세션 ID가 재발급된다(로그아웃 후 이전 세션 ID를 재사용할 수 없다).
 * (3) 이미 로그아웃 상태(빈 세션)에서 호출해도 예외 없이 동일하게 동작한다.
 * (4) 로그인 상태에서 로그아웃하면 주입된 `AuditRecorder`로 module=auth,
 *     action=logout 감사 이벤트가 기록된다(태스크 0714).
 * (5) 이미 로그아웃 상태(빈 세션)에서 호출하면 기록할 행위자가 없으므로
 *     감사 이벤트를 기록하지 않는다.
 * (6) 감사 기록이 예외를 던져도 로그아웃 처리(302, 세션 비움)는 그대로
 *     성공해야 한다 — 방어적 try/catch.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\AuditRecorder;
use MintWiki\Security\LogoutHandler;
use MintWiki\Security\SessionUserResolver;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

// (1)+(2) 로그인 상태에서 로그아웃하면 세션이 비워지고 302로 리다이렉트, 세션 ID가 재발급되어야 한다.
try {
    $_SESSION = [
        SessionUserResolver::SESSION_KEY => 'account-123',
        'csrf_tokens' => ['some-token' => true],
    ];

    $sessionIdBefore = session_id();
    $handler = new LogoutHandler();
    $response = $handler->handle();
    $sessionIdAfter = session_id();

    if ($response->status() !== 302) {
        $failures[] = '로그아웃 처리는 302를 반환해야 하는데 ' . $response->status() . '이었다.';
    }
    if (($response->headers()['Location'] ?? null) !== '/') {
        $failures[] = '로그아웃 처리 성공 시 Location은 "/"이어야 한다.';
    }
    if ($_SESSION !== []) {
        $failures[] = '로그아웃 처리 이후 세션이 완전히 비워져야 한다.';
    }
    if ($sessionIdBefore === $sessionIdAfter) {
        $failures[] = '로그아웃 처리 이후 세션 ID가 재발급되어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)+(2) 로그인 상태 로그아웃 테스트 중 예외: ' . $e->getMessage();
}

// (3) 이미 로그아웃 상태(빈 세션)에서 호출해도 동일하게 동작해야 한다.
try {
    $_SESSION = [];

    $handler2 = new LogoutHandler();
    $response2 = $handler2->handle();

    if ($response2->status() !== 302) {
        $failures[] = '이미 로그아웃 상태에서도 302를 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
    if ($_SESSION !== []) {
        $failures[] = '이미 로그아웃 상태에서 호출해도 세션은 빈 상태를 유지해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(3) 이미 로그아웃 상태 테스트 중 예외: ' . $e->getMessage();
}

// (4) 로그인 상태에서 로그아웃하면 주입된 AuditRecorder로 감사 이벤트가
// 기록되어야 한다.
try {
    $_SESSION = [SessionUserResolver::SESSION_KEY => 'account-456'];

    $mockAuditRecorder4 = new class implements AuditRecorder {
        /** @var AuditEvent[] */
        public array $recordedEvents = [];

        public function record(AuditEvent $event): void
        {
            $this->recordedEvents[] = $event;
        }
    };

    $handler4 = new LogoutHandler(null, $mockAuditRecorder4);
    $response4 = $handler4->handle();

    if ($response4->status() !== 302) {
        $failures[] = '(4) 감사 recorder가 주입되어도 로그아웃은 302를 반환해야 하는데 ' . $response4->status() . '이었다.';
    }
    if (count($mockAuditRecorder4->recordedEvents) !== 1) {
        $failures[] = '(4) 로그인 상태의 로그아웃은 감사 이벤트가 정확히 1건 기록되어야 하는데 '
            . count($mockAuditRecorder4->recordedEvents) . '건이었다.';
    } else {
        $recordedEvent4 = $mockAuditRecorder4->recordedEvents[0];
        if ($recordedEvent4->module() !== 'auth' || $recordedEvent4->action() !== 'logout') {
            $failures[] = '(4) 감사 이벤트는 module=auth, action=logout이어야 한다.';
        }
        if ($recordedEvent4->actorId() !== 'account-456') {
            $failures[] = '(4) 감사 이벤트의 actorId는 로그아웃 전 세션의 계정 id여야 한다.';
        }
        if (($recordedEvent4->metadata()['entity_id'] ?? null) !== 'account-456') {
            $failures[] = '(4) 감사 이벤트 metadata의 entity_id는 로그아웃한 계정 id여야 한다.';
        }
    }
} catch (Exception $e) {
    $failures[] = '(4) 로그아웃 감사 기록 테스트 중 예외: ' . $e->getMessage();
}

// (5) 이미 로그아웃 상태(빈 세션)에서 호출하면 감사 이벤트를 기록하지 않아야 한다.
try {
    $_SESSION = [];

    $mockAuditRecorder5 = new class implements AuditRecorder {
        /** @var AuditEvent[] */
        public array $recordedEvents = [];

        public function record(AuditEvent $event): void
        {
            $this->recordedEvents[] = $event;
        }
    };

    $handler5 = new LogoutHandler(null, $mockAuditRecorder5);
    $response5 = $handler5->handle();

    if ($response5->status() !== 302) {
        $failures[] = '(5) 이미 로그아웃 상태에서도 302를 반환해야 하는데 ' . $response5->status() . '이었다.';
    }
    if ($mockAuditRecorder5->recordedEvents !== []) {
        $failures[] = '(5) 이미 로그아웃 상태(행위자 없음)에서는 감사 이벤트를 기록하면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(5) 이미 로그아웃 상태 감사 기록 테스트 중 예외: ' . $e->getMessage();
}

// (6) 감사 기록이 예외를 던져도 로그아웃 처리는 그대로 성공해야 한다.
try {
    $_SESSION = [SessionUserResolver::SESSION_KEY => 'account-789'];

    $failingAuditRecorder6 = new class implements AuditRecorder {
        public function record(AuditEvent $event): void
        {
            throw new \Exception('Audit recording failure');
        }
    };

    $handler6 = new LogoutHandler(null, $failingAuditRecorder6);
    $response6 = $handler6->handle();

    if ($response6->status() !== 302) {
        $failures[] = '(6) 감사 기록이 실패해도 로그아웃은 302를 반환해야 하는데 ' . $response6->status() . '이었다.';
    }
    if ($_SESSION !== []) {
        $failures[] = '(6) 감사 기록이 실패해도 세션은 비워져야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(6) 감사 기록 실패 방어 테스트 중 예외: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "LogoutHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LogoutHandler 테스트 통과.\n");
exit(0);
