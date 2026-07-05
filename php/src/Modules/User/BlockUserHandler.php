<?php

declare(strict_types=1);

namespace MintWiki\User;

use MintWiki\Http\Response;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\BlockUserFormPage;

/**
 * `POST /admin/users/block` 제출을 처리한다 (태스크 0699).
 *
 * 처리 순서:
 * 1. CSRF 토큰을 검증한다 — 실패하면 아무 것도 바꾸지 않고 403으로 폼을 다시 보여준다.
 * 2. user_id/reason 입력을 검증한다 — user_id가 비어있거나 `account`에 없는
 *    계정을 가리키면, reason이 비어있으면 각각 폼 오류로 표시한다.
 * 3. 검증을 통과하면 `AccountRepository::block()`으로 계정을 차단 상태로
 *    표시하고, 폼으로 302 리다이렉트한다.
 *
 * 차단 사유(reason)는 현재 스키마에 저장하지 않는다 — 차단 사유 정책은
 * 이 태스크의 범위 밖이다.
 */
final class BlockUserHandler
{
    private CsrfTokenService $csrfTokenService;
    private BlockUserFormPage $formPage;

    public function __construct(
        private readonly AccountRepository $accountRepository,
        ?CsrfTokenService $csrfTokenService = null,
        ?BlockUserFormPage $formPage = null
    ) {
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formPage = $formPage ?? new BlockUserFormPage();
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

        $errors = $this->validate($formData);
        if ($errors !== []) {
            return Response::html($this->formPage->render($errors), 422);
        }

        $this->accountRepository->block(trim((string) $formData['user_id']));

        return new Response(302, ['Location' => '/admin/users/block']);
    }

    /**
     * @param array<string, mixed> $formData
     * @return array<string, string> 필드명 => 오류 메시지
     */
    private function validate(array $formData): array
    {
        $errors = [];

        $userId = $formData['user_id'] ?? '';
        if (!is_string($userId) || trim($userId) === '') {
            $errors['user_id'] = '사용자 ID를 입력하세요.';
        } elseif ($this->accountRepository->findById(trim($userId)) === null) {
            $errors['user_id'] = '사용자를 찾을 수 없습니다.';
        }

        $reason = $formData['reason'] ?? '';
        if (!is_string($reason) || trim($reason) === '') {
            $errors['reason'] = '차단 사유는 필수입니다.';
        }

        return $errors;
    }
}
