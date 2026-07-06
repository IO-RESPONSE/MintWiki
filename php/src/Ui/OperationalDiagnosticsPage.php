<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\App\ConfigLoader;
use MintWiki\App\LocalConfigLoader;
use MintWiki\App\SensitiveDiagnosticsFilter;

/**
 * 운영 진단 page의 서버 렌더링 (태스크 0590, 실데이터 연결은 0717).
 *
 * DB 상태, 스키마 상태, 캐시 상태 등 운영 관련 진단 정보를 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다. 0717부터
 * `MintWiki\App\OperationalDiagnosticsCollector`가 조립한 실데이터를
 * `render()`의 `$diagnostics` 인자로 주입받는다 — 인자를 생략하면(직접
 * 인스턴스화하는 단위 테스트 등) DB/스키마/캐시가 모두 "확인되지 않음"
 * 상태의 안전한 기본값으로 대체된다.
 */
final class OperationalDiagnosticsPage
{
    private Escaper $escaper;
    private Layout $layout;
    private string $appVersion;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null, ?string $appVersion = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->appVersion = $appVersion ?? $this->readAppVersion();
    }

    /**
     * 운영 진단 page를 렌더링한다.
     *
     * @param array{
     *     db?: array{status: string, version: string},
     *     schema?: array{status: string, migration: string},
     *     cache?: array{status: string, usage: string},
     *     environment?: array<string, string>
     * }|null $diagnostics `OperationalDiagnosticsCollector::collect()`가 반환하는 구조의 실데이터
     */
    public function render(?array $diagnostics = null): string
    {
        $diagnostics ??= [];

        $appVersionSection = $this->renderAppVersionSection();
        $dbStatusSection = $this->renderDatabaseStatusSection($diagnostics['db'] ?? $this->defaultDatabaseDiagnostics());
        $schemaStatusSection = $this->renderSchemaStatusSection($diagnostics['schema'] ?? $this->defaultSchemaDiagnostics());
        $cacheStatusSection = $this->renderCacheStatusSection($diagnostics['cache'] ?? $this->defaultCacheDiagnostics());
        $filePermissionSection = $this->renderFilePermissionSection();
        $environmentExportSection = $this->renderEnvironmentExportSection(
            $diagnostics['environment'] ?? $this->defaultEnvironmentDiagnostics(),
        );

        $body = '<main>'
            . '<h1>운영 진단</h1>'
            . $appVersionSection
            . $dbStatusSection
            . $schemaStatusSection
            . $cacheStatusSection
            . $filePermissionSection
            . $environmentExportSection
            . '</main>';

        return $this->layout->render('운영 진단', $body);
    }

    /**
     * 애플리케이션 버전 섹션을 렌더링한다.
     */
    private function renderAppVersionSection(): string
    {
        return '<section aria-label="애플리케이션 버전">'
            . '<h2>애플리케이션</h2>'
            . '<dl>'
            . '<dt>버전</dt><dd>' . $this->escaper->html($this->appVersion) . '</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * 데이터베이스 상태 섹션을 렌더링한다.
     *
     * @param array{status: string, version: string} $diagnostics
     */
    private function renderDatabaseStatusSection(array $diagnostics): string
    {
        return '<section aria-label="데이터베이스 상태">'
            . '<h2>데이터베이스</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>' . $this->escaper->html($diagnostics['status']) . '</dd>'
            . '<dt>버전</dt><dd>' . $this->escaper->html($diagnostics['version']) . '</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * 스키마 상태 섹션을 렌더링한다.
     *
     * @param array{status: string, migration: string} $diagnostics
     */
    private function renderSchemaStatusSection(array $diagnostics): string
    {
        return '<section aria-label="스키마 상태">'
            . '<h2>스키마</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>' . $this->escaper->html($diagnostics['status']) . '</dd>'
            . '<dt>마이그레이션</dt><dd>' . $this->escaper->html($diagnostics['migration']) . '</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * 캐시 상태 섹션을 렌더링한다.
     *
     * @param array{status: string, usage: string} $diagnostics
     */
    private function renderCacheStatusSection(array $diagnostics): string
    {
        return '<section aria-label="캐시 상태">'
            . '<h2>캐시</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>' . $this->escaper->html($diagnostics['status']) . '</dd>'
            . '<dt>사용 현황</dt><dd>' . $this->escaper->html($diagnostics['usage']) . '</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * `$diagnostics` 인자가 없을 때 쓰는 데이터베이스 상태 기본값 — 아직
     * `OperationalDiagnosticsCollector`가 실행되지 않았음을 뜻하므로
     * "확인 전"으로 표시한다.
     *
     * @return array{status: string, version: string}
     */
    private function defaultDatabaseDiagnostics(): array
    {
        return ['status' => '확인 전', 'version' => '-'];
    }

    /**
     * @return array{status: string, migration: string}
     */
    private function defaultSchemaDiagnostics(): array
    {
        return ['status' => '확인 전', 'migration' => '-'];
    }

    /**
     * @return array{status: string, usage: string}
     */
    private function defaultCacheDiagnostics(): array
    {
        return ['status' => '확인 전', 'usage' => '-'];
    }

    /**
     * 파일 권한 진단 연결 섹션을 렌더링한다.
     */
    private function renderFilePermissionSection(): string
    {
        return '<section aria-label="파일 권한 진단">'
            . '<h2>파일 권한</h2>'
            . '<p>공유 호스팅 배포에 필요한 파일과 디렉터리 권한을 확인합니다.</p>'
            . '<p><a href="/admin/diagnostics/files">파일 권한 진단 보기</a></p>'
            . '</section>';
    }

    /**
     * 환경 진단 export 섹션을 렌더링한다 — export 다운로드 링크와 미리보기 표.
     *
     * @param array<string, string> $diagnostics 환경 진단 값
     */
    private function renderEnvironmentExportSection(array $diagnostics): string
    {
        $html = '<section aria-label="환경 진단 export">'
            . '<h2>환경 진단 export</h2>'
            . '<p>지원 요청에 첨부할 환경 진단 export 파일을 다운로드합니다.</p>'
            . '<p>민감 정보는 export 대상에서 제외됩니다.</p>'
            . '<p><a href="/admin/diagnostics/export">환경 진단 export 다운로드</a></p>'
            . '<table>'
            . '<thead><tr>'
            . '<th scope="col">항목</th>'
            . '<th scope="col">값</th>'
            . '</tr></thead>'
            . '<tbody>';

        foreach (SensitiveDiagnosticsFilter::filter($diagnostics) as $key => $value) {
            $html .= '<tr>'
                . '<th scope="row">' . $this->escaper->html($key) . '</th>'
                . '<td>' . $this->escaper->html($value) . '</td>'
                . '</tr>';
        }

        return $html . '</tbody></table></section>';
    }

    /**
     * `$diagnostics['environment']` 인자가 없을 때 쓰는 환경 진단 기본값.
     * APP_ENV는 `ConfigLoader`(환경변수 `WIKI_ENVIRONMENT` 또는 설정 파일의
     * `environment` 값)로 실제 조회하며, 아무 것도 설정되어 있지 않으면
     * `.env.sample`과 동일한 기본값 "production"으로 대체한다.
     *
     * @return array<string, string>
     */
    private function defaultEnvironmentDiagnostics(): array
    {
        $appEnv = (new ConfigLoader((new LocalConfigLoader())->load()))->get('environment', 'production');

        return [
            'APP_VERSION' => $this->appVersion,
            'PHP_VERSION' => PHP_VERSION,
            'PHP_SAPI' => PHP_SAPI,
            'APP_ENV' => is_string($appEnv) ? $appEnv : 'production',
        ];
    }

    /**
     * 패키지 VERSION 파일에서 애플리케이션 버전을 읽는다.
     */
    private function readAppVersion(): string
    {
        $versionFile = dirname(__DIR__, 2) . '/VERSION';
        $version = is_file($versionFile) ? file_get_contents($versionFile) : false;

        if ($version === false) {
            return 'unknown';
        }

        $normalizedVersion = trim($version);

        return $normalizedVersion === '' ? 'unknown' : $normalizedVersion;
    }
}
