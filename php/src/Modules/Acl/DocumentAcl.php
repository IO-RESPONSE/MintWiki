<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 특정 문서에 직접 적용되는 ACL 규칙 집합을 나타내는 도메인 모델 (태스크 0687).
 *
 * Python `DocumentAcl`(src/modules/acl/document_acl.py)과 필드를 맞춘다.
 * 네임스페이스 기본 규칙(`NamespaceAclDefaults`)과 달리, 이 모델은 하나의
 * 문서 id에 결부된 규칙 목록만을 관리한다. 규칙이 없을 때 네임스페이스
 * 기본값으로 대체할지 여부는 `AclService`가 판단한다.
 */
final class DocumentAcl
{
    /**
     * @var Rule[]
     */
    private array $rules;

    /**
     * @param Rule[] $rules
     */
    public function __construct(private readonly string $documentId, array $rules = [])
    {
        if (trim($documentId) === '') {
            throw new EmptyDocumentIdError('문서 id는 비어있을 수 없습니다');
        }

        $this->rules = array_values($rules);
    }

    public function documentId(): string
    {
        return $this->documentId;
    }

    public function addRule(Rule $rule): void
    {
        $this->rules[] = $rule;
    }

    /**
     * 문서에서 주어진 id의 규칙을 제거한다. 없으면 아무 동작도 하지 않는다.
     */
    public function removeRule(string $ruleId): void
    {
        $this->rules = array_values(array_filter(
            $this->rules,
            static fn (Rule $rule): bool => $rule->id() !== $ruleId
        ));
    }

    /**
     * @return Rule[]
     */
    public function rules(): array
    {
        return $this->rules;
    }

    public function hasRules(): bool
    {
        return $this->rules !== [];
    }
}
