<?php

declare(strict_types=1);

namespace MintWiki\Security;

use MintWiki\Acl\AclService;
use MintWiki\Acl\Permission;
use MintWiki\Acl\SubjectType;
use MintWiki\Http\Response;
use MintWiki\Ui\Layout;
use MintWiki\Ui\PermissionDeniedPage;

/**
 * 관리자 전용 route를 보호하는 재사용 가능한 인가 게이트 (태스크 0696).
 *
 * 권한 판정은 새 컬럼을 두지 않고 기존 ACL(`AclService::check()`)을 그대로
 * 재사용한다 — 현재 세션의 subject(`SessionUserResolver`가 복원한
 * USER/ANONYMOUS)에 대해 `Permission::Admin`을 검사하고 `Decision`으로
 * 결정한다. `InstallerRouteGate::resolveFrontControllerResponse()`와 동일한
 * "개입이 필요 없으면 null을 반환해 라우팅을 계속한다" 계약을 따른다.
 *
 * 결과는 세 가지로 나뉜다:
 * - 비로그인(익명): `/login`으로 302.
 * - 로그인했으나 관리자가 아님: 403(`PermissionDeniedPage` 재사용).
 * - 관리자: null(호출자가 원래 하려던 라우팅을 계속한다).
 *
 * HTML 렌더링을 직접 만들지 않고 기존 `PermissionDeniedPage`만 재사용한다
 * — 이 게이트의 책임은 인가 판정으로 한정한다.
 */
final class AdminAccessGate
{
    private const LOGIN_REDIRECT_PATH = '/login';

    public function __construct(
        private readonly AclService $aclService,
        private readonly SessionUserResolver $sessionUserResolver,
        private readonly ?Layout $layout = null
    ) {
    }

    /**
     * 현재 요청의 사용자가 관리자 route에 접근할 수 있는지 판정한다.
     *
     * @return Response|null 차단해야 하면 Response(302/403), 통과시키려면 null.
     */
    public function authorize(): ?Response
    {
        $currentUser = $this->sessionUserResolver->resolve();
        $subjectType = $currentUser !== null ? SubjectType::User : SubjectType::Anonymous;
        $subjectId = $currentUser?->id();

        $decision = $this->aclService->check(Permission::Admin, $subjectType, $subjectId);

        if ($decision->isAllowed()) {
            return null;
        }

        if ($subjectType === SubjectType::Anonymous) {
            return new Response(302, ['Location' => self::LOGIN_REDIRECT_PATH], '');
        }

        $permissionDeniedPage = new PermissionDeniedPage(null, $this->layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }
}
