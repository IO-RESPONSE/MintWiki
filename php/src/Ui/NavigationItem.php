<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * Navigation 메뉴의 단일 항목을 표현하는 불변 value object (태스크 0550).
 *
 * 각 navigation 항목은 href, label, 선택적인 id(active 상태 판단용),
 * 선택적인 requiredPermission(권한별 표시 용도)을 가진다.
 * id가 null이면 active 상태를 판단할 수 없다.
 * requiredPermission이 null이면 권한 검사 없이 표시된다.
 */
final class NavigationItem
{
    public function __construct(
        private readonly string $href,
        private readonly string $label,
        private readonly ?string $id = null,
        private readonly ?string $requiredPermission = null
    ) {
    }

    public function href(): string
    {
        return $this->href;
    }

    public function label(): string
    {
        return $this->label;
    }

    public function id(): ?string
    {
        return $this->id;
    }

    public function requiredPermission(): ?string
    {
        return $this->requiredPermission;
    }

    /**
     * 주어진 현재 경로(currentPath)에서 이 항목이 활성 상태인지 판단한다.
     *
     * id가 null이면 활성 상태를 판단할 수 없으므로 false를 반환한다.
     * id가 있다면 currentPath가 id와 정확히 일치할 때 활성 상태이다.
     *
     * @param string $currentPath 현재 페이지의 경로 (예: "/admin/status")
     */
    public function isActive(string $currentPath): bool
    {
        if ($this->id === null) {
            return false;
        }

        return $this->id === $currentPath;
    }

    /**
     * 이 항목이 특정 권한을 요구하는지 확인한다.
     */
    public function requiresPermission(): bool
    {
        return $this->requiredPermission !== null;
    }
}
