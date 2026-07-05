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
 *
 * 0708에서 저장 전 미리보기 영역을 추가했다. "미리보기" 버튼은 같은 폼을
 * `formaction`/`formmethod`로 `POST /wiki/{title}/preview`(0708에서 등록)로
 * 보내며, `formnovalidate`를 붙여 title/source가 비어 있어도 미리보기만은
 * 시도할 수 있게 한다. 이는 점진적 향상의 기본값이다 — JS가 없어도 버튼을
 * 누르면 브라우저가 실제로 `/preview`로 이동해 이 클래스가 다시 렌더링한
 * 편집 화면(원래 입력값 그대로 + `$previewHtml`이 채워진 미리보기 영역)을
 * 보여준다. `assets/js/edit-preview.js`가 로드되면 그 이동을 가로채 같은
 * 응답을 fetch로 받아 미리보기 영역만 갱신하고(CSRF 토큰도 응답의 새 값으로
 * 교체), 페이지 전체를 새로고침하지 않는다 — 두 경로 모두 같은 서버
 * 렌더링 결과에 의존하므로 표시가 갈라지지 않는다.
 *
 * 0709에서 textarea 위에 NamuMark 문법 삽입 툴바와, 그 아래 접이식 문법
 * 도움말(치트시트)을 추가했다. 툴바 버튼은 전부 `type="button"`이라 JS 없이는
 * 아무 폼도 제출하지 않는 무동작 버튼일 뿐이고(사용자가 문법을 직접 타이핑하면
 * 되므로 편집/저장 자체는 계속 정상 동작), `assets/js/edit-toolbar.js`가
 * 로드되면 각 버튼의 `data-markup-before`/`data-markup-after` 속성값으로
 * textarea 선택 영역을 감싸거나 삽입한다. 도움말 패널은 `<details>/<summary>`로
 * 만들어 JS 없이도 순수 HTML/CSS만으로 펼쳐진다.
 */
final class DocumentEditorPage
{
    /**
     * 툴바 버튼 정의. label은 버튼에 표시되는 텍스트, before/after는
     * textarea 선택 영역을 감쌀(또는 삽입할) NamuMark 문법이다(0709 Acceptance
     * Criteria의 문법 목록과 동일).
     *
     * @var list<array{label: string, before: string, after: string}>
     */
    private const TOOLBAR_BUTTONS = [
        ['label' => '굵게', 'before' => "'''", 'after' => "'''"],
        ['label' => '기울임', 'before' => "''", 'after' => "''"],
        ['label' => '밑줄', 'before' => '__', 'after' => '__'],
        ['label' => '링크', 'before' => '[[', 'after' => ']]'],
        ['label' => '제목', 'before' => '== ', 'after' => ' =='],
        ['label' => '목록', 'before' => '* ', 'after' => ''],
        ['label' => '표', 'before' => '|| ', 'after' => ' ||'],
    ];

    /**
     * 문법 도움말 예시. 입력(NamuMark source)과 결과(렌더링된 HTML)를
     * 나란히 보여준다. 결과 HTML은 0705/0706 BlockParser/InlineParser의
     * 실제 렌더링 규칙과 동일한, 개발자가 직접 작성한 정적 HTML이다(사용자
     * 입력이 아니므로 escape하지 않는다).
     *
     * @var list<array{input: string, outputHtml: string}>
     */
    private const HELP_EXAMPLES = [
        ['input' => "'''굵게'''", 'outputHtml' => '<strong>굵게</strong>'],
        ['input' => "''기울임''", 'outputHtml' => '<em>기울임</em>'],
        ['input' => '__밑줄__', 'outputHtml' => '<u>밑줄</u>'],
        ['input' => '[[문서제목]]', 'outputHtml' => '<a href="/wiki/문서제목">문서제목</a>'],
        ['input' => '== 제목 ==', 'outputHtml' => '<h2>제목</h2>'],
        ['input' => '* 목록 항목', 'outputHtml' => '<ul><li>목록 항목</li></ul>'],
        ['input' => '||셀1||셀2||', 'outputHtml' => '<table><tbody><tr><td>셀1</td><td>셀2</td></tr></tbody></table>'],
    ];

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
     * @param string $summaryValue 편집 요약 입력 필드에 채울 값(태스크 0707).
     *     title/source와 달리 선택 입력이라 required를 붙이지 않는다 — 빈
     *     값 처리는 저장 경로(POST 핸들러)에서 기본 문자열로 대체한다.
     * @param string|null $previewHtml 미리보기 영역에 채울 렌더링된 HTML(태스크
     *     0708). `NamuMarkDocumentRenderer`(0706)가 만든, 이미 안전하게
     *     escape된 HTML로 간주해 그대로 삽입한다(문서 보기와 동일한 계약).
     *     null이면 미리보기 영역을 빈 상태로 둔다(JS가 채우거나, 아직 한 번도
     *     미리보기를 요청하지 않은 최초 진입 상태).
     */
    public function render(
        string $actionTitle,
        string $titleValue = '',
        string $sourceValue = '',
        bool $isNew = true,
        array $errors = [],
        string $summaryValue = '',
        ?string $previewHtml = null
    ): string {
        $heading = $isNew ? '새 문서 만들기' : '문서 편집';
        $actionUrl = '/wiki/' . rawurlencode($actionTitle) . '/edit';
        $previewActionUrl = '/wiki/' . rawurlencode($actionTitle) . '/preview';
        $escapedAction = $this->escaper->attribute($actionUrl);
        $escapedPreviewAction = $this->escaper->attribute($previewActionUrl);
        $escapedTitleValue = $this->escaper->html($titleValue);
        $escapedSourceValue = $this->escaper->html($sourceValue);
        $escapedSummaryValue = $this->escaper->html($summaryValue);
        $csrfToken = $this->csrfTokenService->generate();
        $escapedCsrfToken = $this->escaper->html($csrfToken);

        $body = '<main>'
            . '<h1>' . $this->escaper->html($heading) . '</h1>'
            . $this->formErrorSummary->render($errors)
            . '<form method="post" action="' . $escapedAction . '" class="document-editor-form">'
            . '<input type="hidden" name="csrf_token" value="' . $escapedCsrfToken . '">'
            . '<label for="title">제목</label>'
            . '<input type="text" id="title" name="title" value="' . $escapedTitleValue . '" required>'
            . '<label for="source">내용</label>'
            . $this->renderToolbar()
            . '<textarea id="source" name="source" required>' . $escapedSourceValue . '</textarea>'
            . $this->renderHelpPanel()
            . '<label for="summary">편집 요약</label>'
            . '<input type="text" id="summary" name="summary" value="' . $escapedSummaryValue . '" maxlength="500">'
            . '<button type="submit">저장</button>'
            . '<button type="submit" formaction="' . $escapedPreviewAction . '" formmethod="post" formnovalidate '
            . 'class="document-editor-preview-button">미리보기</button>'
            . '</form>'
            . '<section class="edit-preview" id="edit-preview" aria-live="polite">'
            . '<h2>미리보기</h2>'
            . '<div class="document-content" id="edit-preview-content">' . ($previewHtml ?? '') . '</div>'
            . '</section>'
            . '<script src="/assets/js/edit-preview.js" defer></script>'
            . '<script src="/assets/js/edit-toolbar.js" defer></script>'
            . '</main>';

        return $this->layout->render($heading, $body);
    }

    /**
     * NamuMark 문법 삽입 툴바를 렌더링한다. 각 버튼은 `type="button"`이라
     * JS 없이는 폼을 제출하지 않는 무동작 버튼일 뿐이고,
     * `assets/js/edit-toolbar.js`가 `data-markup-before`/`data-markup-after`
     * 속성을 읽어 textarea 선택 영역에 문법을 감싸거나 삽입한다.
     */
    private function renderToolbar(): string
    {
        $buttonsHtml = '';
        foreach (self::TOOLBAR_BUTTONS as $button) {
            $escapedLabel = $this->escaper->html($button['label']);
            $escapedBefore = $this->escaper->attribute($button['before']);
            $escapedAfter = $this->escaper->attribute($button['after']);
            $buttonsHtml .= '<button type="button" class="editor-toolbar__button" '
                . 'data-markup-before="' . $escapedBefore . '" data-markup-after="' . $escapedAfter . '" '
                . 'aria-label="' . $escapedLabel . ' 서식 삽입">' . $escapedLabel . '</button>';
        }

        return '<div class="editor-toolbar" role="toolbar" aria-label="문법 삽입 도구모음" aria-controls="source">'
            . $buttonsHtml
            . '</div>';
    }

    /**
     * 접이식 문법 도움말(치트시트)을 렌더링한다. `<details>/<summary>`라
     * JS 없이도 클릭만으로 펼쳐진다.
     */
    private function renderHelpPanel(): string
    {
        $examplesHtml = '';
        foreach (self::HELP_EXAMPLES as $example) {
            $escapedInput = $this->escaper->html($example['input']);
            $examplesHtml .= '<div class="editor-help__example">'
                . '<code class="editor-help__input">' . $escapedInput . '</code>'
                . '<span class="editor-help__arrow" aria-hidden="true">&rarr;</span>'
                . '<div class="editor-help__output">' . $example['outputHtml'] . '</div>'
                . '</div>';
        }

        return '<details class="editor-help">'
            . '<summary>문법 도움말</summary>'
            . '<div class="editor-help__examples">' . $examplesHtml . '</div>'
            . '</details>';
    }
}
