<?php

declare(strict_types=1);

/**
 * MintWiki\Audit\AuditEvent 도메인 모델의 기본 동작과 append-only 계약을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0410
 * CommentTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\EmptyAuditEventActionError;
use MintWiki\Audit\EmptyAuditEventIdError;
use MintWiki\Audit\EmptyAuditEventModuleError;

$failures = [];

$occurredAt = new \DateTimeImmutable('2026-01-01T00:00:00+00:00');
$event = new AuditEvent(
    'event1',
    'document',
    'document.created',
    $occurredAt,
    'user1',
    ['document_id' => 'doc1']
);

if ($event->id() !== 'event1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($event->module() !== 'document') {
    $failures[] = 'module()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($event->action() !== 'document.created') {
    $failures[] = 'action()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($event->occurredAt() !== $occurredAt) {
    $failures[] = 'occurredAt()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($event->actorId() !== 'user1') {
    $failures[] = 'actorId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($event->metadata() !== ['document_id' => 'doc1']) {
    $failures[] = 'metadata()가 생성자에 전달한 값을 반환하지 않았다.';
}

$eventWithoutOptionalFields = new AuditEvent('event2', 'jobs', 'job.failed', $occurredAt);

if ($eventWithoutOptionalFields->actorId() !== null) {
    $failures[] = 'actorId() 기본값은 null이어야 한다.';
}
if ($eventWithoutOptionalFields->metadata() !== []) {
    $failures[] = 'metadata() 기본값은 빈 배열이어야 한다.';
}

// append-only 계약: 값을 바꾸는 메서드가 하나도 없어야 한다 (readonly 필드만).
$reflection = new \ReflectionClass(AuditEvent::class);
foreach ($reflection->getProperties() as $property) {
    if (!$property->isReadOnly()) {
        $failures[] = "AuditEvent::\${$property->getName()}는 readonly여야 append-only 계약을 지킬 수 있다.";
    }
}

try {
    new AuditEvent('', 'document', 'document.created', $occurredAt);
    $failures[] = '빈 id는 EmptyAuditEventIdError를 던져야 한다.';
} catch (EmptyAuditEventIdError $e) {
    // 예상된 동작.
}

try {
    new AuditEvent('event3', '   ', 'document.created', $occurredAt);
    $failures[] = '공백만 있는 module은 EmptyAuditEventModuleError를 던져야 한다.';
} catch (EmptyAuditEventModuleError $e) {
    // 예상된 동작.
}

try {
    new AuditEvent('event4', 'document', '   ', $occurredAt);
    $failures[] = '공백만 있는 action은 EmptyAuditEventActionError를 던져야 한다.';
} catch (EmptyAuditEventActionError $e) {
    // 예상된 동작.
}

if ($failures !== []) {
    fwrite(STDERR, "AuditEvent 도메인 모델 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AuditEvent 도메인 모델 테스트 통과.\n");
exit(0);
