<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * Navigation 메뉴를 관리하는 불변 컬렉션 (태스크 0550).
 *
 * 여러 NavigationItem을 보유하고, 활성 상태 판단, 권한별 필터링을 제공한다.
 * 현재 경로와 사용자의 권한 집합을 바탕으로 표시할 항목을 결정한다.
 */
final class Navigation
{
    /** @var NavigationItem[] */
    private readonly array $items;

    /**
     * @param NavigationItem[] $items navigation 항목 배열
     */
    public function __construct(array $items = [])
    {
        $this->items = array_values($items);
    }

    /**
     * Navigation에 포함된 모든 항목을 반환한다.
     *
     * @return NavigationItem[]
     */
    public function items(): array
    {
        return $this->items;
    }

    /**
     * 주어진 현재 경로에서 활성 상태인 항목을 찾는다.
     *
     * 활성 상태인 항목이 없으면 null을 반환한다.
     *
     * @param string $currentPath 현재 페이지의 경로 (예: "/admin/status")
     */
    public function findActive(string $currentPath): ?NavigationItem
    {
        foreach ($this->items as $item) {
            if ($item->isActive($currentPath)) {
                return $item;
            }
        }

        return null;
    }

    /**
     * 주어진 권한 목록을 가진 사용자가 볼 수 있는 항목들을 필터링한다.
     *
     * 권한을 요구하지 않는 항목은 항상 포함된다.
     * 권한을 요구하는 항목은 주어진 권한 목록에 포함될 때만 나타난다.
     *
     * @param string[] $allowedPermissions 사용자가 가진 권한 배열
     * @return NavigationItem[] 필터링된 항목 배열
     */
    public function filterByPermissions(array $allowedPermissions): array
    {
        $allowedSet = array_flip($allowedPermissions);

        return array_filter(
            $this->items,
            function (NavigationItem $item) use ($allowedSet): bool {
                if (!$item->requiresPermission()) {
                    return true;
                }

                return isset($allowedSet[$item->requiredPermission()]);
            }
        );
    }

    /**
     * 주어진 경로와 권한으로 활성 상태의 항목을 찾는다.
     *
     * @param string $currentPath 현재 페이지의 경로
     * @param string[] $allowedPermissions 사용자가 가진 권한 배열
     */
    public function findActiveWithPermissions(
        string $currentPath,
        array $allowedPermissions
    ): ?NavigationItem {
        $filtered = $this->filterByPermissions($allowedPermissions);

        foreach ($filtered as $item) {
            if ($item->isActive($currentPath)) {
                return $item;
            }
        }

        return null;
    }
}
