<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 오류 page의 서버 렌더링 (태스크 0592).
 *
 * 404(찾을 수 없음)와 500(서버 오류) page를 HTML로 렌더링한다.
 * 모든 동적 내용은 escaping되어 XSS를 방지한다.
 */
final class ErrorPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 404(찾을 수 없음) page를 렌더링한다.
     */
    public function renderNotFound(string $path = ''): string
    {
        $escapedPath = $this->escaper->html($path);

        $body = '<main>'
            . '<h1>페이지를 찾을 수 없습니다</h1>'
            . '<p>요청한 페이지가 존재하지 않습니다.</p>';

        if ($path !== '') {
            $body .= '<dl>'
                . '<dt>요청 경로:</dt>'
                . '<dd><code>' . $escapedPath . '</code></dd>'
                . '</dl>';
        }

        $body .= '</main>';

        return $this->layout->render('페이지를 찾을 수 없습니다', $body);
    }

    /**
     * 500(서버 오류) page를 렌더링한다.
     */
    public function renderServerError(string $message = ''): string
    {
        $escapedMessage = $this->escaper->html($message);

        $body = '<main>'
            . '<h1>서버 오류</h1>'
            . '<p>서버 오류가 발생했습니다.</p>';

        if ($message !== '') {
            $body .= '<dl>'
                . '<dt>오류 메시지:</dt>'
                . '<dd><code>' . $escapedMessage . '</code></dd>'
                . '</dl>';
        }

        $body .= '</main>';

        return $this->layout->render('서버 오류', $body);
    }
}
