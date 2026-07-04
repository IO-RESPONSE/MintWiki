<?php

declare(strict_types=1);

namespace MintWiki\Security;

use MintWiki\User\AccountRepository;
use MintWiki\User\User;

/**
 * 세션에 저장된 계정 id로 현재 로그인한 사용자를 복원한다 (태스크 0686).
 *
 * `LoginHandler`가 로그인 성공 시 세션에 남긴 계정 id(`SESSION_KEY`)를 읽어
 * `AccountRepository`로 계정 행을 다시 조회하고 `User` value object로
 * 되돌린다. 세션에 값이 없거나(로그인하지 않음) 저장된 id의 계정이 이미
 * 삭제된 경우에는 null을 반환해 익명 사용자로 취급한다.
 */
final class SessionUserResolver
{
    public const SESSION_KEY = 'user_id';

    public function __construct(
        private readonly PhpSessionAdapter $sessionAdapter,
        private readonly AccountRepository $accountRepository
    ) {
    }

    /**
     * 현재 요청의 세션으로부터 로그인한 사용자를 복원한다.
     */
    public function resolve(): ?User
    {
        $accountId = $this->sessionAdapter->get(self::SESSION_KEY);
        if (!is_string($accountId) || $accountId === '') {
            return null;
        }

        $account = $this->accountRepository->findById($accountId);
        if ($account === null) {
            return null;
        }

        return new User($account['id'], $account['username'], $account['display_name']);
    }
}
