<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Acl\Decision;

/**
 * ACL 거부 page의 서버 렌더링 (태스크 0539).
 *
 * 사용자가 요청한 작업에 대한 권한이 없을 때 표시된다.
 * 거부된 권한과 거부 이유를 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class PermissionDeniedPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 권한 거부 page를 렌더링한다.
     *
     * @param Decision $decision ACL 거부 결정
     */
    public function render(Decision $decision): string
    {
        $permission = $this->escaper->html($decision->permission());
        $reason = $this->escaper->html($decision->reason());

        $body = '<main>'
            . '<h1>권한 없음</h1>'
            . '<p>이 작업을 수행할 권한이 없습니다.</p>'
            . '<dl>'
            . '<dt>권한:</dt>'
            . '<dd>' . $permission . '</dd>'
            . '<dt>이유:</dt>'
            . '<dd>' . $reason . '</dd>'
            . '</dl>'
            . '</main>';

        return $this->layout->render('권한 없음', $body);
    }
}
