<?php

declare(strict_types=1);

namespace MintWiki\Security;

use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\AuditRecorder;
use MintWiki\Audit\NoOpAuditRecorder;
use MintWiki\Http\Response;
use Throwable;

/**
 * `GET`/`POST /logout` 요청을 처리한다 (태스크 0686, 감사 로그 기록은 0714).
 *
 * 세션을 완전히 비우고(`PhpSessionAdapter::clear()`) 세션 ID를 재발급한 뒤
 * 홈으로 리다이렉트한다. 이미 로그아웃 상태에서 호출해도 오류 없이 동일하게
 * 동작한다. 세션을 비우기 전에 로그인 상태였다면(계정 id가 있었다면) 감사
 * 이벤트(module=auth, action=logout)를 기록한다 — 이미 익명이었다면 기록할
 * 행위자가 없으므로 건너뛴다. 감사 기록 실패는 로그아웃 처리를 방해하지 않는다.
 */
final class LogoutHandler
{
    private PhpSessionAdapter $sessionAdapter;
    private AuditRecorder $auditRecorder;

    public function __construct(?PhpSessionAdapter $sessionAdapter = null, ?AuditRecorder $auditRecorder = null)
    {
        $this->sessionAdapter = $sessionAdapter ?? new PhpSessionAdapter();
        $this->auditRecorder = $auditRecorder ?? new NoOpAuditRecorder();
    }

    public function handle(): Response
    {
        $accountId = $this->sessionAdapter->get(SessionUserResolver::SESSION_KEY);

        $this->sessionAdapter->clear();
        $this->sessionAdapter->regenerateId();

        if (is_string($accountId) && $accountId !== '') {
            try {
                $this->auditRecorder->record(new AuditEvent(
                    id: self::generateId(),
                    module: 'auth',
                    action: 'logout',
                    occurredAt: new \DateTimeImmutable('now'),
                    actorId: $accountId,
                    metadata: ['entity_id' => $accountId]
                ));
            } catch (Throwable $exception) {
                // 감사 기록 실패는 로그아웃 처리를 방해하지 않음
                \error_log('Audit recording failed: ' . $exception->getMessage());
            }
        }

        return new Response(302, ['Location' => '/']);
    }

    /**
     * UUID v4 문자열을 생성한다 (감사 이벤트 id 발급용).
     */
    private static function generateId(): string
    {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
        $hex = bin2hex($bytes);

        return sprintf(
            '%s-%s-%s-%s-%s',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 12, 4),
            substr($hex, 16, 4),
            substr($hex, 20, 12)
        );
    }
}
