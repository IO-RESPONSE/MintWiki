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

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 운영 진단 page를 렌더링한다.
     */
    public function render(): string
    {
        $dbStatusSection = $this->renderDatabaseStatusSection();
        $schemaStatusSection = $this->renderSchemaStatusSection();
        $cacheStatusSection = $this->renderCacheStatusSection();

        $body = '<main>'
            . '<h1>운영 진단</h1>'
            . $dbStatusSection
            . $schemaStatusSection
            . $cacheStatusSection
            . '</main>';

        return $this->layout->render('운영 진단', $body);
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
}
