<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * `GET/POST /wiki/{title}/edit`가 사용하는 문서 생성·편집 폼 (태스크 0685).
 *
 * 문서가 있으면 편집, 없으면 새 문서 작성 폼으로 같은 화면을 재사용한다.
 * form action은 URL의 title 세그먼트를 그대로 다시 가리키므로($actionTitle),
 * 편집 중 title 값을 바꿔도 저장 요청은 원래 조회했던 URL로 제출된다.
 * 검증 오류(`$errors`)가 있으면 `FormErrorSummary`로 요약해 보여주고, 입력값은
 * 그대로 보존한다. 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class DocumentEditorPage
{
    private Escaper $escaper;
    private Layout $layout;
    private CsrfTokenService $csrfTokenService;
    private FormErrorSummary $formErrorSummary;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?CsrfTokenService $csrfTokenService = null,
        ?FormErrorSummary $formErrorSummary = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formErrorSummary = $formErrorSummary ?? new FormErrorSummary($this->escaper);
    }

    /**
     * 문서 생성/편집 폼을 렌더링한다.
     *
     * @param string $actionTitle 폼 action에 사용할 title(요청 URL의 title 세그먼트)
     * @param string $titleValue title 입력 필드에 채울 값
     * @param string $sourceValue source textarea에 채울 값
     * @param bool $isNew true면 "새 문서 만들기", false면 "문서 편집" 화면으로 표시
     * @param array<string, string|array<string>> $errors 필드명 => 오류 메시지(들)
     */
    public function render(
        string $actionTitle,
        string $titleValue = '',
        string $sourceValue = '',
        bool $isNew = true,
        array $errors = []
    ): string {
        $heading = $isNew ? '새 문서 만들기' : '문서 편집';
        $actionUrl = '/wiki/' . rawurlencode($actionTitle) . '/edit';
        $escapedAction = $this->escaper->attribute($actionUrl);
        $escapedTitleValue = $this->escaper->html($titleValue);
        $escapedSourceValue = $this->escaper->html($sourceValue);
        $csrfToken = $this->csrfTokenService->generate();
        $escapedCsrfToken = $this->escaper->html($csrfToken);

        $body = '<main>'
            . '<h1>' . $this->escaper->html($heading) . '</h1>'
            . $this->formErrorSummary->render($errors)
            . '<form method="post" action="' . $escapedAction . '">'
            . '<input type="hidden" name="csrf_token" value="' . $escapedCsrfToken . '">'
            . '<label for="title">제목</label>'
            . '<input type="text" id="title" name="title" value="' . $escapedTitleValue . '" required>'
            . '<label for="source">내용</label>'
            . '<textarea id="source" name="source" required>' . $escapedSourceValue . '</textarea>'
            . '<button type="submit">저장</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render($heading, $body);
    }
}
