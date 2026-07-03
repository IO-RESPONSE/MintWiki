<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 백업 page의 서버 렌더링 (태스크 0598).
 *
 * 시스템 백업 및 복구 기능을 관리하는 page이다.
 * shared hosting 환경에서의 안정적인 백업 운영을 고려한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class BackupPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 백업 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>백업</h1>'
            . '<p>백업 및 복구 기능을 준비 중입니다.</p>'
            . '</main>';

        return $this->layout->render('백업', $body);
    }
}
