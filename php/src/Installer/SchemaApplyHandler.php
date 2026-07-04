<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use MintWiki\App\AppBootstrap;
use MintWiki\Http\Response;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\InstallSchemaApplyPage;
use MintWiki\Ui\Layout;
use Throwable;

/**
 * `POST /install/schema` 제출을 처리한다 (태스크 0680).
 *
 * 처리 순서:
 * 1. CSRF 토큰을 검증한다 — 실패하면 아무 것도 적용하지 않고 진행 화면으로 되돌아간다.
 * 2. `AppBootstrap`(태스크 0673)으로 0679가 기록한 DB 설정을 읽어 PDO를 얻는다 —
 *    설정이 없거나 접속이 실패하면 적용을 시도하지 않고 오류를 표시한다.
 * 3. `SchemaApply`로 `db/schema`의 SQL을 FK 의존 순서로 적용한다. 실패하면
 *    예외를 잡아 진행 화면에 오류로 표시하고 다음 단계로 넘어가지 않는다.
 * 4. 성공하면(`schema_version`이 채워지면) 다음 단계(관리자 계정 생성, 태스크 0681)로
 *    이동하는 링크를 보여준다.
 */
final class SchemaApplyHandler
{
    private CsrfTokenService $csrfTokenService;
    private SchemaApply $schemaApply;
    private AppBootstrap $appBootstrap;
    private InstallSchemaApplyPage $page;
    private Layout $layout;
    private string $schemaVersion;

    public function __construct(
        ?CsrfTokenService $csrfTokenService = null,
        ?SchemaApply $schemaApply = null,
        ?AppBootstrap $appBootstrap = null,
        ?InstallSchemaApplyPage $page = null,
        ?Layout $layout = null,
        ?string $schemaVersion = null
    ) {
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->schemaApply = $schemaApply ?? new SchemaApply();
        $this->appBootstrap = $appBootstrap ?? new AppBootstrap();
        $this->page = $page ?? new InstallSchemaApplyPage();
        $this->layout = $layout ?? new Layout();
        $this->schemaVersion = $schemaVersion ?? $this->readAppVersion();
    }

    /**
     * @param array<string, mixed> $formData `$_POST` 배열.
     */
    public function handle(array $formData): Response
    {
        $csrfToken = $formData['csrf_token'] ?? '';
        if (!is_string($csrfToken) || !$this->csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $this->page->render('CSRF 토큰이 유효하지 않습니다. 화면을 새로고침한 뒤 다시 시도하세요.'),
                403
            );
        }

        try {
            $pdo = $this->appBootstrap->pdo();
        } catch (Throwable $exception) {
            $pdo = null;
        }

        if ($pdo === null) {
            return Response::html(
                $this->page->render('데이터베이스에 접속할 수 없습니다. 이전 단계에서 접속 정보를 다시 확인하세요.'),
                422
            );
        }

        try {
            $this->schemaApply->apply($pdo, $this->schemaVersion);
        } catch (Throwable $exception) {
            return Response::html($this->page->render('스키마 적용에 실패했습니다: ' . $exception->getMessage()), 500);
        }

        return Response::html($this->renderSuccess());
    }

    private function renderSuccess(): string
    {
        $body = '<main>'
            . '<h1>스키마 적용 완료</h1>'
            . '<p>데이터베이스에 위키 테이블을 생성했습니다.</p>'
            . '<p><a href="/install/admin-account">다음 단계: 관리자 계정 생성</a></p>'
            . '</main>';

        return $this->layout->render('스키마 적용 완료', $body);
    }

    /**
     * `php/VERSION` 파일에서 스키마 적용 시 기록할 버전 문자열을 읽는다.
     */
    private function readAppVersion(): string
    {
        $versionFile = dirname(__DIR__, 2) . '/VERSION';
        $version = is_file($versionFile) ? file_get_contents($versionFile) : false;

        return $version === false ? 'unknown' : trim($version);
    }
}
