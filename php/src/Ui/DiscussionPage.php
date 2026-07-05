<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\Thread;
use MintWiki\Document\Document;
use MintWiki\Security\CsrfTokenService;

/**
 * 문서의 토론 page 서버 렌더링 (태스크 0548, 라우트 연결·댓글/새 스레드 폼
 * 주입은 0712).
 *
 * 문서의 모든 토론 스레드 목록을 시간순으로 표시하고, 각 스레드마다 그
 * 스레드의 댓글 목록과 댓글 작성 form(`CommentFormPage::renderForm()`,
 * Layout으로 다시 감싸지 않은 조각)을 함께 보여준다. 맨 위에는 새 스레드를
 * 시작하는 form을 둔다 — `POST /wiki/{title}/discussion`(0712)로 제출된다.
 * thread/댓글이 없는 경우 각각 "thread 없음"/"댓글 없음" 상태를 표시한다.
 * `$isAuthorized`가 false면(로그인하지 않았거나 토론 쓰기 권한이 없는 경우)
 * 새 스레드 form과 모든 댓글 form 대신 로그인 안내를 보여준다 — 실제 쓰기
 * 권한(discuss) 판단은 route가 하고, 이 page는 그 결과만 반영한다.
 * 모든 사용자 입력(문서 title, 스레드 제목, 작성자 id, 댓글 본문 등)은
 * escaping되어 XSS를 방지한다.
 */
final class DiscussionPage
{
    private Escaper $escaper;
    private Layout $layout;
    private CsrfTokenService $csrfTokenService;
    private FormErrorSummary $formErrorSummary;
    private CommentFormPage $commentFormPage;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?CsrfTokenService $csrfTokenService = null,
        ?FormErrorSummary $formErrorSummary = null,
        ?CommentFormPage $commentFormPage = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formErrorSummary = $formErrorSummary ?? new FormErrorSummary();
        $this->commentFormPage = $commentFormPage ?? new CommentFormPage(
            $this->escaper,
            null,
            $this->csrfTokenService,
            $this->formErrorSummary
        );
    }

    /**
     * 토론 page를 렌더링한다.
     *
     * @param Document $document 조회한 문서
     * @param Thread[] $threads 문서의 토론 스레드 목록
     * @param array<string, Comment[]> $commentsByThreadId 스레드 id => 댓글 목록
     * @param array<string, string|array<string>> $newThreadErrors 새 스레드 form 검증 오류
     * @param array<string, array<string, string|array<string>>> $commentErrorsByThreadId 스레드 id => 댓글 form 검증 오류
     * @param bool $isAuthorized 새 스레드/댓글 form을 보여줄지(토론 쓰기 권한이 있는지) 여부
     */
    public function render(
        Document $document,
        array $threads = [],
        array $commentsByThreadId = [],
        array $newThreadErrors = [],
        array $commentErrorsByThreadId = [],
        bool $isAuthorized = true
    ): string {
        $title = $this->escaper->html($document->title());

        $newThreadForm = $this->renderNewThreadForm($document, $newThreadErrors, $isAuthorized);
        $threadList = $this->renderThreadList($document, $threads, $commentsByThreadId, $commentErrorsByThreadId, $isAuthorized);

        $body = '<main>'
            . '<h1>' . $title . ' - 토론</h1>'
            . $newThreadForm
            . $threadList
            . '</main>';

        return $this->layout->render('문서 토론', $body);
    }

    /**
     * 새 토론 스레드를 시작하는 form을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors
     */
    private function renderNewThreadForm(Document $document, array $errors, bool $isAuthorized): string
    {
        if (!$isAuthorized) {
            return '<section>'
                . '<h2>새 토론 시작하기</h2>'
                . '<p>토론을 시작하려면 로그인이 필요합니다.</p>'
                . '<a href="/login">로그인</a>'
                . '</section>';
        }

        $actionEscaped = $this->escaper->attribute('/wiki/' . rawurlencode($document->title()) . '/discussion');
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        return '<section>'
            . '<h2>새 토론 시작하기</h2>'
            . $errorSummary
            . '<form method="post" action="' . $actionEscaped . '">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="new-thread-title">제목</label>'
            . '<input type="text" id="new-thread-title" name="title" required>'
            . '<button type="submit">토론 시작</button>'
            . '</form>'
            . '</section>';
    }

    /**
     * 스레드 목록을 렌더링한다.
     *
     * @param Thread[] $threads 스레드 배열
     * @param array<string, Comment[]> $commentsByThreadId
     * @param array<string, array<string, string|array<string>>> $commentErrorsByThreadId
     */
    private function renderThreadList(
        Document $document,
        array $threads,
        array $commentsByThreadId,
        array $commentErrorsByThreadId,
        bool $isAuthorized
    ): string {
        if (empty($threads)) {
            return '<p>thread 없음</p>';
        }

        $html = '<ul>';
        foreach ($threads as $thread) {
            $comments = $commentsByThreadId[$thread->id()] ?? [];
            $commentErrors = $commentErrorsByThreadId[$thread->id()] ?? [];
            $html .= $this->renderThreadItem($document, $thread, $comments, $commentErrors, $isAuthorized);
        }
        $html .= '</ul>';

        return $html;
    }

    /**
     * 단일 스레드 항목(제목/작성자/상태 + 댓글 목록 + 댓글 form)을 렌더링한다.
     *
     * @param Comment[] $comments
     * @param array<string, string|array<string>> $commentErrors
     */
    private function renderThreadItem(
        Document $document,
        Thread $thread,
        array $comments,
        array $commentErrors,
        bool $isAuthorized
    ): string {
        $threadId = $this->escaper->html($thread->id());
        $threadTitle = $this->escaper->html($thread->title());
        $createdBy = $this->escaper->html($thread->createdBy());
        $status = $this->escaper->html($thread->status());

        $commentList = $this->renderCommentList($comments);
        $commentForm = $this->commentFormPage->renderForm($document->title(), $thread->id(), $commentErrors, $isAuthorized);

        return '<li>'
            . 'ID: ' . $threadId
            . ' | 제목: ' . $threadTitle
            . ' | 작성자: ' . $createdBy
            . ' | 상태: ' . $status
            . $commentList
            . $commentForm
            . '</li>';
    }

    /**
     * 스레드의 댓글 목록을 렌더링한다.
     *
     * @param Comment[] $comments
     */
    private function renderCommentList(array $comments): string
    {
        if (empty($comments)) {
            return '<p>댓글 없음</p>';
        }

        $html = '<ul>';
        foreach ($comments as $comment) {
            $body = $this->escaper->html($comment->body());
            $createdBy = $this->escaper->html($comment->createdBy());
            $html .= '<li>' . $createdBy . ': ' . $body . '</li>';
        }
        $html .= '</ul>';

        return $html;
    }
}
