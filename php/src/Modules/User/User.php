<?php

declare(strict_types=1);

namespace MintWiki\User;

/**
 * 로그인한 사용자를 표현하는 불변 value object (태스크 0409).
 *
 * id, username, displayName 세 필드로 Python `User`(src/modules/user/model.py)와
 * 필드를 맞춘다. displayName은 선택 필드로 기본값은 null이다. AnonymousIdentity/
 * IpIdentity와 달리 isAnonymous 속성을 갖지 않는다 — manifest
 * (src/modules/user/manifest.json)가 고정한 경계다.
 */
final class User
{
    private readonly string $username;

    public function __construct(
        private readonly string $id,
        string $username,
        private readonly ?string $displayName = null
    ) {
        if (trim($username) === '') {
            throw new EmptyUsernameError('사용자명은 비어있을 수 없습니다');
        }

        $this->username = $username;
    }

    public function id(): string
    {
        return $this->id;
    }

    public function username(): string
    {
        return $this->username;
    }

    public function displayName(): ?string
    {
        return $this->displayName;
    }
}
