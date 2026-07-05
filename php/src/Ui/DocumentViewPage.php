<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Render\DocumentRenderer;
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Ui\SeoMetadata;

/**
 * 단일 문서 view page의 서버 렌더링 (태스크 0529, 0582, 0684, 0692).
 *
 * 존재하는 문서를 표시하거나, 없는 경우 나무위키풍 빈 문서 안내를 보여준다.
 * 모든 사용자 입력(문서 title 등)은 escaping되어 XSS를 방지한다.
 * 문서 source는 DocumentRenderer를 통해 HTML로 렌더링되며, 렌더러가 생성한
 * HTML은 이미 안전하게 처리되어 있다 (태스크 0582).
 * 0684에서 `render()`에 `$requestedTitle`을 추가했다 — `GET /wiki/{title}`가
 * 존재하지 않는 제목으로 조회될 때 그 제목을 안내/편집 링크에 사용하기
 * 위함이다.
 * 0692에서 `DocumentHeader`(제목 + 나무위키식 액션 탭)를 두 화면 모두에
 * 도입했다. 문서가 없는 경우에는 `/documents/new`(라우트가 실제로 연결된 적
 * 없는 경로)로 가던 예전 "만들기" 링크 대신, 이미 연결되어 있는
 * `/wiki/{title}/edit`로 이어지는 `EmptyState`를 재사용해 나무위키 빈 문서
 * UX(제목 + 안내 문구 + 편집 링크)를 보여준다. `$currentPath`는 액션 탭의
 * 활성 상태 판단에, `$lastEditedBy`는 헤더의 "마지막 편집" 메타 정보 표시
 * 여부에 쓰인다 — 둘 다 알 수 없으면(빈 문자열/null) 생략된다.
 * 0706에서 기본 렌더러를 `PlainTextDocumentRenderer`에서
 * `NamuMarkDocumentRenderer`로 바꿨다 — 저장된 위키 문법('''굵게'''/[[링크]]/
 * 표/제목 등)이 실제 HTML(+ 제목이 2개 이상이면 목차)로 렌더링된다. 목차는
 * `NamuMarkDocumentRenderer`가 본문 HTML 앞에 붙여 반환하므로, 이 클래스는
 * `$renderResult->html()`을 `.document-content` wrapper로 감싸 배치하기만
 * 하면 된다 — 스킨 CSS(`assets/css/document-content.css`)가 이 클래스명으로
 * 본문/표/목차 스타일을 범위 한정한다.
 */
final class DocumentViewPage
{
    private Escaper $escaper;
    private Layout $layout;
    private DocumentRenderer $renderer;
    private DocumentHeader $documentHeader;
    private EmptyState $emptyState;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?DocumentRenderer $renderer = null,
        ?DocumentHeader $documentHeader = null,
        ?EmptyState $emptyState = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->renderer = $renderer ?? new NamuMarkDocumentRenderer();
        $this->documentHeader = $documentHeader ?? new DocumentHeader($this->escaper);
        $this->emptyState = $emptyState ?? new EmptyState($this->escaper);
    }

    /**
     * 문서 view page를 렌더링한다.
     *
     * @param Document|null $document 조회한 문서, 없으면 null
     * @param string|null $source 문서의 source 내용, 없으면 placeholder 표시
     * @param string|null $requestedTitle 문서가 없을 때 사용자가 조회하려 했던 제목.
     *                                    제공되면 404 화면에 제목/편집 링크를 표시한다.
     * @param string $currentPath 현재 페이지의 경로 (액션 탭 활성 표시 판단용)
     * @param string|null $lastEditedBy 마지막 편집자 정보, 알 수 없으면 생략한다
     */
    public function render(
        ?Document $document,
        ?string $source = null,
        ?string $requestedTitle = null,
        string $currentPath = '',
        ?string $lastEditedBy = null
    ): string {
        if ($document === null) {
            return $this->renderNotFound($requestedTitle, $currentPath);
        }

        return $this->renderDocument($document, $source, $currentPath, $lastEditedBy);
    }

    /**
     * 존재하는 문서를 렌더링한다.
     */
    private function renderDocument(
        Document $document,
        ?string $source = null,
        string $currentPath = '',
        ?string $lastEditedBy = null
    ): string {
        $header = $this->documentHeader->render($document->title(), $currentPath, $lastEditedBy);

        // source가 제공되면 렌더러로 렌더링, 아니면 placeholder
        if ($source !== null) {
            try {
                $renderResult = $this->renderer->render($source);
                $contentHtml = $renderResult->html();
            } catch (\Throwable $e) {
                // 렌더링 실패 시 fallback: source를 escape하여 표시
                $contentHtml = $this->renderFallback($source);
            }
        } else {
            $contentHtml = '<p>문서 내용이 여기에 표시됩니다.</p>';
        }

        $body = '<main>'
            . $header
            . '<div class="document-content">' . $contentHtml . '</div>'
            . '</main>';

        $seo = new SeoMetadata(
            $document->title(),
            $this->extractDescription($source),
            '/docs/' . $document->id()
        );

        return $this->layout->render($document->title(), $body, 'ko', null, $seo);
    }

    /**
     * 렌더링 실패 시 fallback을 렌더링한다.
     *
     * source를 escape하여 사용자가 볼 수 있도록 표시하고,
     * 렌더링 오류 안내를 제공한다.
     */
    private function renderFallback(string $source): string
    {
        $escapedSource = $this->escaper->html($source);
        return '<div class="render-fallback">'
            . '<p class="render-fallback-message">문서 렌더링에 실패했습니다. 아래는 원본 소스입니다:</p>'
            . '<pre class="render-fallback-source">' . $escapedSource . '</pre>'
            . '</div>';
    }

    /**
     * 문서를 찾을 수 없을 때의 page를 렌더링한다.
     *
     * $requestedTitle이 주어지면(공백만 있는 경우는 제외) 나무위키식 빈 문서
     * 안내(제목 + "이 문서는 아직 없습니다" + 편집 탭/링크)를 보여준다. 알 수
     * 없으면(라우트가 title을 추출하지 못한 경우 등) 일반적인 "문서를 찾을 수
     * 없습니다" 메시지로 대체한다.
     */
    private function renderNotFound(?string $requestedTitle = null, string $currentPath = ''): string
    {
        if ($requestedTitle === null || trim($requestedTitle) === '') {
            $body = '<main>'
                . '<h1>문서를 찾을 수 없습니다</h1>'
                . '<p>요청하신 문서가 존재하지 않습니다.</p>'
                . '</main>';

            return $this->layout->render('문서를 찾을 수 없습니다', $body);
        }

        $header = $this->documentHeader->render($requestedTitle, $currentPath);
        $editHref = '/wiki/' . rawurlencode($requestedTitle) . '/edit';
        $emptyStateHtml = $this->emptyState->render(
            '이 문서는 아직 없습니다. 편집하여 만들 수 있습니다.',
            null,
            ['href' => $editHref, 'label' => '편집']
        );

        $body = '<main>' . $header . $emptyStateHtml . '</main>';

        return $this->layout->render($requestedTitle, $body);
    }

    /**
     * source에서 meta description으로 사용할 텍스트를 추출한다.
     *
     * 첫 160 글자 이내의 텍스트를 사용하며, 줄바꿈은 공백으로 정규화된다.
     * source가 null이거나 비어있으면 null을 반환한다.
     */
    private function extractDescription(?string $source): ?string
    {
        if ($source === null || trim($source) === '') {
            return null;
        }

        $text = trim($source);
        $text = preg_replace('/\s+/', ' ', $text) ?? $text;

        $maxLength = 160;
        if (strlen($text) > $maxLength) {
            $text = substr($text, 0, $maxLength) . '...';
        }

        return $text;
    }
}
