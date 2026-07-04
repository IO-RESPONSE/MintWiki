<?php

declare(strict_types=1);

namespace MintWiki\Installer;

use MintWiki\Http\Response;
use MintWiki\Persistence\ConnectionConfig;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\InstallDBFormPage;
use MintWiki\Ui\Layout;
use Throwable;

/**
 * `POST /install/database` 제출을 처리한다 (태스크 0679).
 *
 * 처리 순서:
 * 1. CSRF 토큰을 검증한다 — 실패하면 아무 것도 기록하지 않고 폼으로 되돌아간다.
 * 2. 필수 입력값(host/port/dbname/username/password)을 검증한다.
 * 3. `DatabaseConfigWriter::testConnection()`으로 실제 접속을 시험한다 — 실패하면
 *    폼으로 되돌아가 오류를 표시하고 아무 것도 기록하지 않는다.
 * 4. 접속에 성공하면 `DatabaseConfigWriter::write()`로 `local-config.php`를
 *    기록하고, 다음 단계(스키마 적용, 태스크 0680)로 이동하는 링크를 보여준다.
 *
 * 비밀번호는 응답 본문에 그대로 노출하지 않는다 — 접속 실패 메시지는 항상
 * 고정된 안내 문구만 사용하고, 예외 상세는 응답에 담지 않는다.
 */
final class DatabaseSetupHandler
{
    private CsrfTokenService $csrfTokenService;
    private DatabaseConfigWriter $configWriter;
    private InstallDBFormPage $formPage;
    private Layout $layout;

    public function __construct(
        ?CsrfTokenService $csrfTokenService = null,
        ?DatabaseConfigWriter $configWriter = null,
        ?InstallDBFormPage $formPage = null,
        ?Layout $layout = null
    ) {
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->configWriter = $configWriter ?? new DatabaseConfigWriter();
        $this->formPage = $formPage ?? new InstallDBFormPage();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * @param array<string, mixed> $formData `$_POST` 배열.
     */
    public function handle(array $formData): Response
    {
        $csrfToken = $formData['csrf_token'] ?? '';
        if (!is_string($csrfToken) || !$this->csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $this->formPage->render(['csrf_token' => 'CSRF 토큰이 유효하지 않습니다. 폼을 새로고침한 뒤 다시 시도하세요.']),
                403
            );
        }

        $errors = $this->validate($formData);
        if ($errors !== []) {
            return Response::html($this->formPage->render($errors), 422);
        }

        $connectionConfig = new ConnectionConfig(
            'mysql',
            trim((string) $formData['host']),
            (int) $formData['port'],
            trim((string) $formData['dbname']),
            trim((string) $formData['username']),
            (string) $formData['password']
        );

        try {
            $this->configWriter->testConnection($connectionConfig);
        } catch (Throwable $exception) {
            return Response::html(
                $this->formPage->render(['connection' => '입력한 정보로 데이터베이스에 접속할 수 없습니다. 접속 정보를 확인한 뒤 다시 시도하세요.']),
                422
            );
        }

        $this->configWriter->write($connectionConfig);

        return Response::html($this->renderSuccess());
    }

    /**
     * @param array<string, mixed> $formData
     * @return array<string, string> 필드명 => 오류 메시지
     */
    private function validate(array $formData): array
    {
        $errors = [];

        $host = $formData['host'] ?? '';
        if (!is_string($host) || trim($host) === '') {
            $errors['host'] = '호스트를 입력하세요.';
        }

        $port = $formData['port'] ?? '';
        $portString = is_scalar($port) ? trim((string) $port) : '';
        if ($portString === '' || !ctype_digit($portString)) {
            $errors['port'] = '포트는 숫자로 입력하세요.';
        }

        $dbname = $formData['dbname'] ?? '';
        if (!is_string($dbname) || trim($dbname) === '') {
            $errors['dbname'] = '데이터베이스명을 입력하세요.';
        }

        $username = $formData['username'] ?? '';
        if (!is_string($username) || trim($username) === '') {
            $errors['username'] = '사용자명을 입력하세요.';
        }

        $password = $formData['password'] ?? '';
        if (!is_string($password) || $password === '') {
            $errors['password'] = '비밀번호를 입력하세요.';
        }

        return $errors;
    }

    private function renderSuccess(): string
    {
        $body = '<main>'
            . '<h1>데이터베이스 설정 완료</h1>'
            . '<p>데이터베이스 접속 정보를 저장했습니다.</p>'
            . '<p><a href="/install/schema">다음 단계: 스키마 적용</a></p>'
            . '</main>';

        return $this->layout->render('데이터베이스 설정 완료', $body);
    }
}
