<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * ACL 권한 검사 결과를 표현하는 불변 value object (태스크 0408).
 *
 * permission, allowed, reason, matchedRuleId 네 필드로 Python `Decision`
 * (src/modules/acl/decision.py)과 계약을 맞춘다 — src/modules/acl/manifest.json
 * 이 고정한 "출력 Decision 은 permission/allowed/reason/matched_rule_id
 * 네 필드를 가진다"는 계약과 동일하다. 태스크 노트가 말하는
 * allow/reason/action/resource 는 이 모델에서 각각 allowed/reason/
 * permission/matchedRuleId 필드에 대응한다. reason은 사람이 읽는 문장이
 * 아니라 acl.matched_rule / acl.no_matching_rule 같은 안정적인 code
 * 문자열이다. 여러 규칙을 조합해 이 결과를 산출하는 로직은 이 모델이 아닌
 * ACL 서비스가 담당한다.
 */
final class Decision
{
    public function __construct(
        private readonly string $permission,
        private readonly bool $allowed,
        private readonly string $reason,
        private readonly ?string $matchedRuleId = null
    ) {
    }

    public function permission(): string
    {
        return $this->permission;
    }

    public function isAllowed(): bool
    {
        return $this->allowed;
    }

    public function isDenied(): bool
    {
        return !$this->allowed;
    }

    public function reason(): string
    {
        return $this->reason;
    }

    public function matchedRuleId(): ?string
    {
        return $this->matchedRuleId;
    }
}
