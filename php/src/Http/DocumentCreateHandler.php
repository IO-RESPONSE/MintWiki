<?php

declare(strict_types=1);

namespace MintWiki\Http;

use MintWiki\Document\Service;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\Escaper;

/**
 * POST /documents 요청을 처리하는 문서 생성 핸들러 (태스크 0531).
 *
 * 사용자가 제출한 title을 받아서 DocumentService.create()를 호출하고,
 * 성공 시 생성된 문서를 표시하고, 실패 시 에러 메시지를 반환한다.
 * 입력 데이터는 모두 escape되어 XSS를 방지한다.
 */
final class DocumentCreateHandler
{
    public function __construct(
        private readonly Service $documentService,
        private readonly DocumentViewPage $documentViewPage = new DocumentViewPage()
    ) {
    }

    /**
     * 문서 생성 요청을 처리한다.
     *
     * @param string $title 사용자가 입력한 문서 제목
     * @return Response 성공 시 생성된 문서, 실패 시 에러 메시지
     */
    public function handle(string $title): Response
    {
        try {
            $document = $this->documentService->create($title);

            // 생성 성공 — 문서 view page 렌더링
            $html = $this->documentViewPage->render($document);

            return Response::html($html, 201);
        } catch (EmptyTitleError) {
            return Response::html(
                $this->renderError('제목이 비어있습니다.'),
                400
            );
        } catch (DuplicateNormalizedTitleError) {
            $escaper = new Escaper();
            return Response::html(
                $this->renderError('이미 존재하는 제목입니다: ' . $escaper->html($title)),
                409
            );
        }
    }

    /**
     * 에러 메시지를 렌더링한다.
     */
    private function renderError(string $message): string
    {
        $escapedMessage = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');

        return '<!doctype html>'
            . '<html lang="ko">'
            . '<head>'
            . '<meta charset="UTF-8">'
            . '<meta name="viewport" content="width=device-width, initial-scale=1">'
            . '<title>오류</title>'
            . '</head>'
            . '<body>'
            . '<main>'
            . '<h1>오류</h1>'
            . '<p>' . $escapedMessage . '</p>'
            . '<a href="/documents/new">다시 시도</a>'
            . '</main>'
            . '</body>'
            . '</html>';
    }
}
