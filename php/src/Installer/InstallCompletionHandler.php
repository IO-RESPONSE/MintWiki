<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use MintWiki\Http\Response;
use MintWiki\Ui\InstallCompletionPage;

/**
 * `GET /install/complete` 요청을 처리한다 (태스크 0682).
 *
 * 관리자 계정 생성(태스크 0681) 이후 이 route에 도달하면 `InstallerLock`으로
 * 설치 완료를 기록해 재설치를 막고, `InstallCompletionPage`로 완료 화면을
 * 보여준다. 이미 lock이 기록되어 있으면(재호출) 완료 시각을 다시 쓰지 않고
 * 화면만 보여준다 — `InstallerRouteGate`가 lock을 이유로 이 route를 다시
 * 막기 전까지 재호출되어도 안전해야 하기 때문이다.
 */
final class InstallCompletionHandler
{
    private InstallerLock $installerLock;
    private InstallCompletionPage $page;

    public function __construct(?InstallerLock $installerLock = null, ?InstallCompletionPage $page = null)
    {
        $this->installerLock = $installerLock ?? InstallerLock::atDefaultPath();
        $this->page = $page ?? new InstallCompletionPage();
    }

    public function handle(): Response
    {
        if (!$this->installerLock->isLocked()) {
            $this->installerLock->markComplete();
        }

        return Response::html($this->page->render());
    }
}
