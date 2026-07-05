<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 운영 진단 page의 서버 렌더링 (태스크 0590).
 *
 * DB 상태, 스키마 상태, 캐시 상태 등 운영 관련 진단 정보를 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
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
     * @param array<string, string>|null $environmentDiagnostics 환경 진단 export 미리보기 값
     */
    public function render(?array $environmentDiagnostics = null): string
    {
        $appVersionSection = $this->renderAppVersionSection();
        $dbStatusSection = $this->renderDatabaseStatusSection();
        $schemaStatusSection = $this->renderSchemaStatusSection();
        $cacheStatusSection = $this->renderCacheStatusSection();
        $filePermissionSection = $this->renderFilePermissionSection();
        $environmentExportSection = $this->renderEnvironmentExportSection(
            $environmentDiagnostics ?? $this->defaultEnvironmentDiagnostics(),
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
     */
    private function renderDatabaseStatusSection(): string
    {
        return '<section aria-label="데이터베이스 상태">'
            . '<h2>데이터베이스</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>연결 중</dd>'
            . '<dt>버전</dt><dd>placeholder</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * 스키마 상태 섹션을 렌더링한다.
     */
    private function renderSchemaStatusSection(): string
    {
        return '<section aria-label="스키마 상태">'
            . '<h2>스키마</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>검증 중</dd>'
            . '<dt>마이그레이션</dt><dd>placeholder</dd>'
            . '</dl>'
            . '</section>';
    }

    /**
     * 캐시 상태 섹션을 렌더링한다.
     */
    private function renderCacheStatusSection(): string
    {
        return '<section aria-label="캐시 상태">'
            . '<h2>캐시</h2>'
            . '<dl>'
            . '<dt>상태</dt><dd>대기 중</dd>'
            . '<dt>사용 현황</dt><dd>placeholder</dd>'
            . '</dl>'
            . '</section>';
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
     * 환경 진단 export placeholder 섹션을 렌더링한다.
     *
     * @param array<string, string> $diagnostics 환경 진단 값
     */
    private function renderEnvironmentExportSection(array $diagnostics): string
    {
        $html = '<section aria-label="환경 진단 export">'
            . '<h2>환경 진단 export</h2>'
            . '<p>지원 요청에 첨부할 환경 진단 export 파일 생성을 준비 중입니다.</p>'
            . '<p>민감 정보는 export 대상에서 제외됩니다.</p>'
            . '<button type="button" disabled>진단 export 준비 중</button>'
            . '<table>'
            . '<thead><tr>'
            . '<th scope="col">항목</th>'
            . '<th scope="col">값</th>'
            . '</tr></thead>'
            . '<tbody>';

        foreach ($this->safeEnvironmentDiagnostics($diagnostics) as $key => $value) {
            $html .= '<tr>'
                . '<th scope="row">' . $this->escaper->html($key) . '</th>'
                . '<td>' . $this->escaper->html($value) . '</td>'
                . '</tr>';
        }

        return $html . '</tbody></table></section>';
    }

    /**
     * 기본 환경 진단 export placeholder 값을 반환한다.
     *
     * @return array<string, string>
     */
    private function defaultEnvironmentDiagnostics(): array
    {
        return [
            'APP_VERSION' => $this->appVersion,
            'PHP_VERSION' => PHP_VERSION,
            'PHP_SAPI' => PHP_SAPI,
            'APP_ENV' => 'placeholder',
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

    /**
     * 민감한 환경 값이 export preview에 포함되지 않도록 제외한다.
     *
     * @param array<string, string> $diagnostics 환경 진단 값
     *
     * @return array<string, string>
     */
    private function safeEnvironmentDiagnostics(array $diagnostics): array
    {
        $safeDiagnostics = [];

        foreach ($diagnostics as $key => $value) {
            if ($this->isSensitiveEnvironmentKey($key)) {
                continue;
            }

            $safeDiagnostics[$key] = $value;
        }

        return $safeDiagnostics;
    }

    /**
     * 환경 변수 이름만 보고 민감 정보 가능성이 큰 항목을 판정한다.
     */
    private function isSensitiveEnvironmentKey(string $key): bool
    {
        $pattern = '/(password|passwd|secret|token|credential|auth|cookie|session'
            . '|api[_-]?key|private[_-]?key|(^|[_-])key($|[_-]))/i';

        return preg_match($pattern, $key) === 1;
    }
}
