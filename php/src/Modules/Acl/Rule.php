<?php

declare(strict_types=1);

namespace MintWiki\Acl;

use DateTimeImmutable;

/**
 * 문서에 대한 하나의 ACL 규칙을 나타내는 도메인 모델 (태스크 0687).
 *
 * Python `Rule`(src/modules/acl/rule.py)과 필드를 맞춘다. 규칙은
 * 대상(subjectType/subjectId), 검사 대상 권한(permission), 허용/거부
 * 여부(effect)로 구성된다. 여러 규칙을 조합해 최종 접근 허용 여부를
 * 판단하는 로직은 이 모델이 아닌 `AclService`가 담당한다.
 *
 * expiresAt이 있는 규칙의 만료 여부(isExpired)는 이 클래스가 계산만
 * 제공할 뿐, 실제로 걸러내는 책임은 규칙 목록을 구성하는 호출자(예:
 * `PdoRepository`)에게 있다 — `AclService::check()`는 now 인자를 받지
 * 않으므로 만료를 검사하지 않는다(Python 쪽과 동일한 계약).
 */
final class Rule
{
    public function __construct(
        private readonly string $id,
        private readonly SubjectType $subjectType,
        private readonly Permission $permission,
        private readonly Effect $effect,
        private readonly ?string $subjectId = null,
        private readonly ?DateTimeImmutable $expiresAt = null
    ) {
        if (trim($id) === '') {
            throw new EmptyRuleIdError('규칙 id는 비어있을 수 없습니다');
        }

        if (
            in_array($subjectType, [SubjectType::User, SubjectType::Group], true)
            && ($subjectId === null || trim($subjectId) === '')
        ) {
            throw new MissingSubjectIdError('대상 종류가 사용자 또는 그룹인 경우 subject_id가 필요합니다');
        }
    }

    public function id(): string
    {
        return $this->id;
    }

    public function subjectType(): SubjectType
    {
        return $this->subjectType;
    }

    public function subjectId(): ?string
    {
        return $this->subjectId;
    }

    public function permission(): Permission
    {
        return $this->permission;
    }

    public function effect(): Effect
    {
        return $this->effect;
    }

    public function expiresAt(): ?DateTimeImmutable
    {
        return $this->expiresAt;
    }

    public function isAllow(): bool
    {
        return $this->effect === Effect::Allow;
    }

    public function isTemporary(): bool
    {
        return $this->expiresAt !== null;
    }

    public function isExpired(DateTimeImmutable $now): bool
    {
        if ($this->expiresAt === null) {
            return false;
        }

        return $now >= $this->expiresAt;
    }

    /**
     * 주어진 대상이 이 규칙의 적용 대상인지 확인한다.
     */
    public function appliesTo(SubjectType $subjectType, ?string $subjectId = null): bool
    {
        if ($this->subjectType === SubjectType::All) {
            return true;
        }

        if ($this->subjectType !== $subjectType) {
            return false;
        }

        if (in_array($this->subjectType, [SubjectType::User, SubjectType::Group], true)) {
            return $this->subjectId === $subjectId;
        }

        return true;
    }
}
