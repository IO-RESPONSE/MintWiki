<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use MintWiki\Acl\Effect;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\App\AppBootstrap;
use MintWiki\Http\Response;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\Layout;
use MintWiki\User\AccountRepository;
use Throwable;

/**
 * `POST /install/admin` 제출을 처리한다 (태스크 0681).
 *
 * 처리 순서:
 * 1. CSRF 토큰을 검증한다 — 실패하면 아무 것도 생성하지 않고 폼으로 되돌아간다.
 * 2. `AppBootstrap`(태스크 0673)으로 0679/0680이 준비한 DB에 접속한다 — 접속할
 *    수 없으면 계정을 생성하지 않고 오류를 표시한다.
 * 3. 입력값(username/email/password/password_confirm)을 검증하고, username
 *    중복 여부를 `AccountRepository`로 확인한다.
 * 4. 검증을 통과하면 `password_hash()`로 해시한 뒤 `AccountRepository::create()`로
 *    `account` 테이블에 관리자 계정을 생성한다.
 * 5. 생성한 계정 id에 `Acl\PdoRepository::grantNamespacePermission()`으로
 *    `Permission::Admin` 허용 규칙을 부여한다(태스크 0696) — `account`
 *    테이블에 role/is_admin 컬럼을 두지 않고 기존 ACL을 그대로 정본으로
 *    쓰기 때문에, 이 단계가 없으면 어떤 사용자도 관리자 게이트
 *    (`Security\AdminAccessGate`)를 통과할 수 없다.
 *
 * 비밀번호는 로그나 응답 본문에 그대로 노출하지 않는다 — 검증 오류 메시지는
 * 항상 고정된 안내 문구만 사용하고, 해시 전 평문은 이 클래스 밖으로 전달되지
 * 않는다.
 */
final class AdminAccountSetupHandler
{
    private CsrfTokenService $csrfTokenService;
    private AppBootstrap $appBootstrap;
    private InstallAdminAccountFormPage $formPage;
    private Layout $layout;

    public function __construct(
        ?CsrfTokenService $csrfTokenService = null,
        ?AppBootstrap $appBootstrap = null,
        ?InstallAdminAccountFormPage $formPage = null,
        ?Layout $layout = null
    ) {
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->appBootstrap = $appBootstrap ?? new AppBootstrap();
        $this->formPage = $formPage ?? new InstallAdminAccountFormPage();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * @param array<string, mixed> $formData `$_POST` 배열.
     */
    public function handle(array $formData): Response
    {
        $csrfToken = $formData['csrf_token'] ?? '';
        if (!is_string($csrfToken) || !$this->csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $this->formPage->render(['csrf_token' => 'CSRF 토큰이 유효하지 않습니다. 폼을 새로고침한 뒤 다시 시도하세요.']),
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
                $this->formPage->render(['database' => '데이터베이스에 접속할 수 없습니다. 이전 단계에서 접속 정보를 다시 확인하세요.']),
                422
            );
        }

        $accountRepository = new AccountRepository($pdo);

        $errors = $this->validate($formData, $accountRepository);
        if ($errors !== []) {
            return Response::html($this->formPage->render($errors), 422);
        }

        $passwordHash = password_hash((string) $formData['password'], PASSWORD_DEFAULT);
        $accountId = $accountRepository->create(trim((string) $formData['username']), $passwordHash);

        (new AclPdoRepository($pdo))->grantNamespacePermission(
            NamespaceAclDefaults::DEFAULT_NAMESPACE,
            AclSubjectType::User,
            AclPermission::Admin,
            Effect::Allow,
            $accountId
        );

        return Response::html($this->renderSuccess());
    }

    /**
     * @param array<string, mixed> $formData
     * @return array<string, string> 필드명 => 오류 메시지
     */
    private function validate(array $formData, AccountRepository $accountRepository): array
    {
        $errors = [];

        $username = $formData['username'] ?? '';
        if (!is_string($username) || trim($username) === '') {
            $errors['username'] = '관리자 ID를 입력하세요.';
        } elseif ($accountRepository->usernameExists(trim($username))) {
            $errors['username'] = '이미 사용 중인 관리자 ID입니다.';
        }

        $email = $formData['email'] ?? '';
        if (!is_string($email) || trim($email) === '' || filter_var($email, FILTER_VALIDATE_EMAIL) === false) {
            $errors['email'] = '올바른 이메일 주소를 입력하세요.';
        }

        $password = $formData['password'] ?? '';
        if (!is_string($password) || $password === '') {
            $errors['password'] = '비밀번호를 입력하세요.';
        }

        $passwordConfirm = $formData['password_confirm'] ?? '';
        if (!is_string($passwordConfirm) || $passwordConfirm === '' || $passwordConfirm !== $password) {
            $errors['password_confirm'] = '비밀번호 확인이 일치하지 않습니다.';
        }

        return $errors;
    }

    private function renderSuccess(): string
    {
        $body = '<main>'
            . '<h1>관리자 계정 생성 완료</h1>'
            . '<p>최초 관리자 계정을 생성했습니다.</p>'
            . '<p><a href="/install/complete">다음 단계: 설치 완료</a></p>'
            . '</main>';

        return $this->layout->render('관리자 계정 생성 완료', $body);
    }
}
