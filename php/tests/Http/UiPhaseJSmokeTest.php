<?php

declare(strict_types=1);

/**
 * Phase J(태스크 0704-0712: NamuMark 렌더, 편집 UX, history/discussion)가
 * 실제 배포 자산·Ui 컴포넌트에 빠짐없이 통합되어 있는지 확인하는 연기
 * 테스트(태스크 0713). phpunit 없이 `php` CLI만으로 실행되며, DB/자격
 * 증명 없이 항상 실행할 수 있다(0695 `UiSkinSmokeTest.php`와 동일한 방식) —
 * 개별 기능 단위 테스트(DocumentViewNamuMarkRouteTest.php,
 * EditSummaryFieldTest.php, DocumentEditPreviewRouteTest.php,
 * DiscussionRouteTest.php, DocumentHistoryDiffRouteTest.php 등)와 달리,
 * 네 기능이 배포되는 Ui 컴포넌트/CSS·JS 자산과 함께 실제로 맞물리는지를
 * 한 번에 확인한다.
 *
 * 확인 대상(0713 acceptance criteria):
 * (1) NamuMark 렌더: 굵게/링크/표/제목이 실제 HTML로, 제목이 2개 이상이면
 *     목차(TOC)까지 함께 렌더링되는지.
 * (2) 편집 화면: 요약 입력, 미리보기 영역, 문법 삽입 툴바, 문법 도움말이
 *     모두 나타나는지.
 * (3) history: 리비전 목록이 렌더링되는지.
 * (4) discussion: 스레드/댓글을 실제로 만들고 그 결과가 렌더링되는지.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\InMemoryRepository as DiscussionInMemoryRepository;
use MintWiki\Discussion\Service as DiscussionService;
use MintWiki\Document\Document;
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Revision\Revision;
use MintWiki\Ui\DiscussionPage;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\DocumentHistoryPage;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

// ============================================================================
// (1) NamuMark 렌더: 굵게/링크/표/제목(2개 이상 -> TOC)이 HTML로 렌더링된다.
// ============================================================================

$namuMarkSource = "== 개요 ==\n'''smoke 굵게'''이며 [[다른 문서]]로 이어진다.\n|| a || b ||\n\n== 상세 ==\n추가 내용";

$documentViewPage = new DocumentViewPage(null, null, new NamuMarkDocumentRenderer());
$document = new Document('phase-j-doc', 'Phase J Smoke Test Document');
$viewBody = $documentViewPage->render($document, $namuMarkSource);

if (!str_contains($viewBody, '<strong>smoke 굵게</strong>')) {
    $failures[] = 'GET /wiki/{title} 응답이 굵게 문법을 <strong>으로 렌더링해야 한다(태스크 0704, 0706).';
}
if (!str_contains($viewBody, '<a href="/wiki/' . rawurlencode('다른 문서') . '">다른 문서</a>')) {
    $failures[] = 'GET /wiki/{title} 응답이 내부 링크 문법을 <a>로 렌더링해야 한다(태스크 0704, 0706).';
}
if (!str_contains($viewBody, '<table>')) {
    $failures[] = 'GET /wiki/{title} 응답이 표 문법을 <table>로 렌더링해야 한다(태스크 0705, 0706).';
}
if (!str_contains($viewBody, '<nav class="toc"')) {
    $failures[] = 'GET /wiki/{title} 응답이 제목 2개 이상인 문서의 목차(TOC)를 렌더링해야 한다(태스크 0706).';
}
if (!str_contains($viewBody, '<link rel="stylesheet" href="/assets/css/document-content.css">')) {
    $failures[] = 'GET /wiki/{title} 응답이 document-content.css를 로드해야 한다.';
}

// ============================================================================
// (2) 편집 화면: 요약/미리보기/툴바/문법 도움말이 모두 나타나야 한다.
// ============================================================================

$editorPage = new DocumentEditorPage();
$editBody = $editorPage->render('Phase J Smoke Test Document', 'Phase J Smoke Test Document', $namuMarkSource, false);

if (!str_contains($editBody, '<label for="summary">편집 요약</label>')) {
    $failures[] = '편집 화면이 편집 요약 입력을 포함해야 한다(태스크 0707).';
}
if (!str_contains($editBody, 'class="edit-preview"')) {
    $failures[] = '편집 화면이 미리보기 영역(edit-preview)을 포함해야 한다(태스크 0708).';
}
if (!str_contains($editBody, 'class="editor-toolbar"')) {
    $failures[] = '편집 화면이 문법 삽입 툴바(editor-toolbar)를 포함해야 한다(태스크 0709).';
}
if (!str_contains($editBody, 'class="editor-help"')) {
    $failures[] = '편집 화면이 문법 도움말(editor-help)을 포함해야 한다(태스크 0709).';
}
foreach ([
    '/assets/js/edit-preview.js',
    '/assets/js/edit-toolbar.js',
] as $script) {
    if (!str_contains($editBody, '<script src="' . $script . '" defer></script>')) {
        $failures[] = "편집 화면이 스크립트({$script})를 로드해야 한다.";
    }
}

// ============================================================================
// (3) history: 리비전 목록이 렌더링되어야 한다.
// ============================================================================

$historyPage = new DocumentHistoryPage();
$firstRevision = new Revision('rev-1', 'phase-j-doc', '최초 내용', 'author-1', '최초 작성');
$secondRevision = new Revision('rev-2', 'phase-j-doc', $namuMarkSource, 'author-2', 'NamuMark 문법 추가', $firstRevision->id());
$historyBody = $historyPage->render($document, [$secondRevision, $firstRevision]);

if (!str_contains($historyBody, 'NamuMark 문법 추가')) {
    $failures[] = 'history 화면이 리비전 편집 요약을 렌더링해야 한다(태스크 0707, 0710).';
}
if (!str_contains($historyBody, '최초 버전')) {
    $failures[] = 'history 화면이 부모 리비전이 없는 최초 리비전을 표시해야 한다(태스크 0710).';
}

// ============================================================================
// (4) discussion: 스레드/댓글을 실제로 만들고 렌더링되어야 한다.
// ============================================================================

$discussionRepository = new DiscussionInMemoryRepository();
$discussionService = new DiscussionService($discussionRepository);
$thread = $discussionService->createThread($document->id(), 'Phase J 스모크 스레드', 'smoke-author');
$discussionService->addComment($thread->id(), 'phase j 스모크 댓글', 'smoke-commenter');

$threads = $discussionService->listThreadsByDocumentId($document->id());
$commentsByThreadId = [$thread->id() => $discussionService->listCommentsByThreadId($thread->id())];

$discussionPage = new DiscussionPage();
$discussionBody = $discussionPage->render($document, $threads, $commentsByThreadId);

if (!str_contains($discussionBody, 'Phase J 스모크 스레드')) {
    $failures[] = 'discussion 화면이 생성한 스레드 제목을 렌더링해야 한다(태스크 0711, 0712).';
}
if (!str_contains($discussionBody, 'phase j 스모크 댓글')) {
    $failures[] = 'discussion 화면이 생성한 댓글 본문을 렌더링해야 한다(태스크 0711, 0712).';
}
if (!str_contains($discussionBody, '<form method="post" action="/wiki/')) {
    $failures[] = 'discussion 화면이 새 스레드 작성 form을 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Phase J 통합 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Phase J 통합 연기 테스트 통과.\n");
exit(0);
