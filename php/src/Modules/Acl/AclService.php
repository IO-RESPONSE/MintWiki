<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 문서에 대한 권한 검사를 담당하는 서비스 (태스크 0687).
 *
 * Python `AclService`(src/modules/acl/service.py)와 계약을 맞춘다.
 * 문서별 ACL 규칙(`DocumentAcl`)이 있으면 그것만 사용하고(네임스페이스
 * 기본값과 병합하지 않음), 없으면 네임스페이스 기본 규칙
 * (`NamespaceAclDefaults`)으로 대체한다. 규칙은 등록된 순서대로 검사해
 * 대상과 권한이 모두 일치하는 첫 번째 규칙(first-match-wins)의 effect를
 * 결과로 사용한다.
 *
 * 규칙 만료(`Rule::isExpired()`)나 그룹 소속 검사는 이 서비스가 평가하지
 * 않는다 — 만료 필터링은 규칙 목록을 구성하는 호출자(`PdoRepository`)의
 * 책임이고, 그룹 소속은 호출자가 후보 그룹마다 `check()`를 반복 호출해야
 * 한다(Python 쪽과 동일한 계약, manifest.json 참고).
 */
final class AclService
{
    public const REASON_MATCHED_RULE = 'acl.matched_rule';
    public const REASON_NO_MATCHING_RULE = 'acl.no_matching_rule';

    public function __construct(private readonly ?NamespaceAclDefaults $namespaceDefaults = null)
    {
    }

    /**
     * 주어진 대상이 문서에 대해 특정 권한을 가지는지 검사한다.
     *
     * 일치하는 규칙이 없으면 거부(deny)로 판단하며, 이때 reason은
     * REASON_NO_MATCHING_RULE이다. 규칙이 일치하면 reason은
     * REASON_MATCHED_RULE이고, 어떤 규칙인지는 matchedRuleId로 알 수 있다.
     */
    public function check(
        Permission $permission,
        SubjectType $subjectType,
        ?string $subjectId = null,
        ?DocumentAcl $documentAcl = null,
        string $namespace = NamespaceAclDefaults::DEFAULT_NAMESPACE
    ): Decision {
        foreach ($this->resolveRules($documentAcl, $namespace) as $rule) {
            if ($rule->permission() !== $permission) {
                continue;
            }
            if (!$rule->appliesTo($subjectType, $subjectId)) {
                continue;
            }

            return new Decision($permission->value, $rule->isAllow(), self::REASON_MATCHED_RULE, $rule->id());
        }

        return new Decision($permission->value, false, self::REASON_NO_MATCHING_RULE);
    }

    /**
     * 검사에 사용할 규칙 목록을 결정한다.
     *
     * @return Rule[]
     */
    private function resolveRules(?DocumentAcl $documentAcl, string $namespace): array
    {
        if ($documentAcl !== null && $documentAcl->hasRules()) {
            return $documentAcl->rules();
        }

        if ($this->namespaceDefaults !== null) {
            return $this->namespaceDefaults->get($namespace);
        }

        return [];
    }
}
