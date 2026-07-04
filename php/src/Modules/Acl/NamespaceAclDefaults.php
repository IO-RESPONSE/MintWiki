<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 네임스페이스별 기본 ACL 규칙 집합을 관리한다 (태스크 0687).
 *
 * Python `NamespaceAclDefaults`(src/modules/acl/namespace_defaults.py)와
 * 계약을 맞춘다. 문서에 별도의 ACL 규칙이 없을 때 네임스페이스 단위로
 * 적용할 기본 규칙을 등록하고 조회한다.
 */
final class NamespaceAclDefaults
{
    public const DEFAULT_NAMESPACE = '*';

    /**
     * @var array<string, Rule[]>
     */
    private array $rulesByNamespace = [];

    /**
     * @param Rule[] $rules
     */
    public function register(string $namespace, array $rules): void
    {
        $this->rulesByNamespace[$namespace] = array_values($rules);
    }

    /**
     * 네임스페이스에 등록된 기본 규칙을 반환한다.
     *
     * 해당 네임스페이스에 등록된 규칙이 없으면 DEFAULT_NAMESPACE에 등록된
     * 규칙을 반환하고, 그마저도 없으면 빈 목록을 반환한다.
     *
     * @return Rule[]
     */
    public function get(string $namespace): array
    {
        if (array_key_exists($namespace, $this->rulesByNamespace)) {
            return $this->rulesByNamespace[$namespace];
        }

        return $this->rulesByNamespace[self::DEFAULT_NAMESPACE] ?? [];
    }
}
