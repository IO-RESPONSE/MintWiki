<?php

declare(strict_types=1);

namespace MintWiki\Security;

use MintWiki\App\AppBootstrap;
use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\AuditRecorder;
use MintWiki\Audit\NoOpAuditRecorder;
use MintWiki\Http\Response;
use MintWiki\Ui\LoginPage;
use MintWiki\User\AccountRepository;
use Throwable;

/**
 * `POST /login` 제출을 처리한다 (태스크 0686, 감사 로그 기록은 0714).
 *
 * 처리 순서:
 * 1. CSRF 토큰을 검증한다 — 실패하면 자격 증명을 대조하지 않고 폼으로 되돌아간다.
 * 2. `AppBootstrap`으로 DB에 접속한다 — 접속할 수 없으면 로그인할 수 없다는
 *    오류를 보여주고 폼으로 되돌아간다.
 * 3. `AccountRepository`로 username을 조회하고 `password_verify()`로
 *    password_hash를 대조한다.
 * 4. 대조에 성공하면 세션 ID를 재발급(session fixation 방지)한 뒤
 *    `PhpSessionAdapter`에 계정 id를 저장하고, 감사 이벤트(module=auth,
 *    action=login_succeeded)를 기록한 뒤 홈으로 리다이렉트한다. 감사 기록
 *    실패는 로그인 자체를 막지 않는다(방어적 try/catch).
 *
 * 실패 사유(존재하지 않는 아이디/틀린 비밀번호)는 구분해서 노출하지 않는다 —
 * 항상 같은 고정 문구만 보여주고, 평문 비밀번호는 이 클래스 밖으로(로그나
 * 응답 본문으로) 전달되지 않는다.
 */
final class LoginHandler
{
    private CsrfTokenService $csrfTokenService;
    private AppBootstrap $appBootstrap;
    private LoginPage $loginPage;
    private PhpSessionAdapter $sessionAdapter;
    private AuditRecorder $auditRecorder;

    public function __construct(
        ?CsrfTokenService $csrfTokenService = null,
        ?AppBootstrap $appBootstrap = null,
        ?LoginPage $loginPage = null,
        ?PhpSessionAdapter $sessionAdapter = null,
        ?AuditRecorder $auditRecorder = null
    ) {
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->appBootstrap = $appBootstrap ?? new AppBootstrap();
        $this->loginPage = $loginPage ?? new LoginPage();
        $this->sessionAdapter = $sessionAdapter ?? new PhpSessionAdapter();
        $this->auditRecorder = $auditRecorder ?? new NoOpAuditRecorder();
    }

    /**
     * @param array<string, mixed> $formData `$_POST` 배열.
     */
    public function handle(array $formData): Response
    {
        $username = is_string($formData['username'] ?? null) ? $formData['username'] : '';
        $password = is_string($formData['password'] ?? null) ? $formData['password'] : '';

        $csrfToken = $formData['csrf_token'] ?? '';
        if (!is_string($csrfToken) || !$this->csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $this->loginPage->render(['_form' => 'CSRF 토큰이 유효하지 않습니다. 폼을 새로고침한 뒤 다시 시도하세요.'], $username),
                403
            );
        }

        try {
            $pdo = $this->appBootstrap->pdo();
        } catch (Throwable $exception) {
            $pdo = null;
        }

        if ($pdo === null) {
            return Response::html(
                $this->loginPage->render(['_form' => '데이터베이스에 접속할 수 없어 로그인할 수 없습니다.'], $username),
                503
            );
        }

        $accountRepository = new AccountRepository($pdo);
        $account = trim($username) === '' ? null : $accountRepository->findByUsername(trim($username));
        $passwordHash = is_string($account['password_hash'] ?? null) ? $account['password_hash'] : null;

        if ($account === null || $passwordHash === null || $password === '' || !password_verify($password, $passwordHash)) {
            return Response::html(
                $this->loginPage->render(['_form' => '아이디 또는 비밀번호가 올바르지 않습니다.'], $username),
                401
            );
        }

        $this->sessionAdapter->regenerateId();
        $this->sessionAdapter->set(SessionUserResolver::SESSION_KEY, $account['id']);

        try {
            $this->auditRecorder->record(new AuditEvent(
                id: self::generateId(),
                module: 'auth',
                action: 'login_succeeded',
                occurredAt: new \DateTimeImmutable('now'),
                actorId: (string) $account['id'],
                metadata: ['entity_id' => (string) $account['id']]
            ));
        } catch (Throwable $exception) {
            // 감사 기록 실패는 로그인 처리를 방해하지 않음
            \error_log('Audit recording failed: ' . $exception->getMessage());
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
