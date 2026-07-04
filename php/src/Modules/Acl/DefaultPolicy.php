<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 기본 ACL 정책 정의 (태스크 0687).
 *
 * Python `default_policy`(src/modules/acl/default_policy.py)와 계약을
 * 맞춘다. `acl_namespace_rule`에 DEFAULT_NAMESPACE("*") 규칙이 아직
 * 등록되지 않은 경우(신규 설치, seed 데이터 없음)에도 문서 읽기/쓰기가
 * 합리적으로 동작하도록 하는 대체 규칙을 제공한다 — 누구나 읽을 수
 * 있고, 익명 사용자는 편집할 수 없으며, 로그인한 사용자는 편집할 수
 * 있다. 편집 허용 규칙은 대상을 ALL로 지정하므로, 익명 사용자를 먼저
 * 거부하는 규칙이 그보다 앞서 있어야 first-match-wins로 실제 적용된다.
 */
final class DefaultPolicy
{
    public const PUBLIC_READ_RULE_ID = 'default-public-read-allow';
    public const ANONYMOUS_EDIT_DENY_RULE_ID = 'default-anonymous-edit-deny';
    public const LOGGED_IN_EDIT_RULE_ID = 'default-logged-in-edit-allow';

    /**
     * @return Rule[]
     */
    public static function defaultRules(): array
    {
        return [
            new Rule(self::PUBLIC_READ_RULE_ID, SubjectType::All, Permission::Read, Effect::Allow),
            new Rule(self::ANONYMOUS_EDIT_DENY_RULE_ID, SubjectType::Anonymous, Permission::Edit, Effect::Deny),
            new Rule(self::LOGGED_IN_EDIT_RULE_ID, SubjectType::All, Permission::Edit, Effect::Allow),
        ];
    }

    public static function buildDefaultNamespaceAclDefaults(): NamespaceAclDefaults
    {
        $defaults = new NamespaceAclDefaults();
        $defaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, self::defaultRules());

        return $defaults;
    }
}
