<?php

declare(strict_types=1);

namespace MintWiki\Http;

use MintWiki\Document\Service;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\NotFoundError;
use MintWiki\Document\Document;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\IdempotencyKeyService;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\Escaper;

/**
 * POST /documents/{id} 요청을 처리하는 문서 편집 핸들러 (태스크 0533, 0569).
 *
 * 사용자가 제출한 title과 source를 받아서 DocumentService.update()를 호출하고,
 * 새 리비전을 생성한 후 업데이트된 문서를 표시한다.
 * 제목이 중복되거나 문서를 찾을 수 없으면 에러 메시지를 반환한다.
 * 모든 입력 데이터는 escape되어 XSS를 방지한다.
 * Idempotency key를 검증하여 중복 제출을 방지한다 (태스크 0569).
 */
final class DocumentEditHandler
{
    public function __construct(
        private readonly Service $documentService,
        private readonly RevisionRepository $revisionRepository,
        private readonly IdempotencyKeyService $idempotencyKeyService = new IdempotencyKeyService(),
        private readonly DocumentViewPage $documentViewPage = new DocumentViewPage()
    ) {
    }

    /**
     * 문서 편집 요청을 처리한다.
     *
     * @param string $documentId 편집할 문서의 ID
     * @param string $title 수정된 문서 제목
     * @param string $source 수정된 문서 내용
     * @param string $idempotencyKey 중복 제출 방지를 위한 idempotency key
     * @return Response 성공 시 수정된 문서, 실패 시 에러 메시지
     */
    public function handle(string $documentId, string $title, string $source, string $idempotencyKey = ''): Response
    {
        // Idempotency key 검증
        if (!$this->idempotencyKeyService->validate($idempotencyKey)) {
            return Response::html(
                $this->renderError('유효하지 않은 요청입니다.'),
                400
            );
        }

        try {
            // 기존 문서 조회
            $existingDocument = $this->documentService->get($documentId);
            if ($existingDocument === null) {
                return Response::html(
                    $this->renderError('문서를 찾을 수 없습니다.'),
                    404
                );
            }

            // 제목이 변경되었을 경우 유효성 검사
            $newDocument = $existingDocument;
            if ($existingDocument->title() !== $title) {
                $newDocument = new Document($existingDocument->id(), $title, $existingDocument->currentRevisionId());
            }

            // 문서 업데이트
            $updatedDocument = $this->documentService->update($newDocument);

            // 새 리비전 생성
            $newRevision = new Revision(
                id: self::generateId(),
                documentId: $updatedDocument->id(),
                source: $source,
                authorId: '',
                summary: '',
                parentRevisionId: $updatedDocument->currentRevisionId()
            );
            $this->revisionRepository->create($newRevision);

            // 현재 리비전 ID 업데이트
            $updatedDocument = new Document(
                $updatedDocument->id(),
                $updatedDocument->title(),
                $newRevision->id()
            );
            $updatedDocument = $this->documentService->update($updatedDocument);

            // 수정 성공 — 문서 view page 렌더링
            $html = $this->documentViewPage->render($updatedDocument);

            return Response::html($html, 200);
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
        } catch (NotFoundError) {
            return Response::html(
                $this->renderError('문서를 찾을 수 없습니다.'),
                404
            );
        }
    }

    /**
     * UUID v4 문자열을 생성한다 (리비전 id 발급용).
     */
    private static function generateId(): string
    {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
        $hex = bin2hex($bytes);

        return sprintf(
            '%s-%s-%s-%s-%s',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 12, 4),
            substr($hex, 16, 4),
            substr($hex, 20, 12)
        );
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
            . '<a href="/documents">돌아가기</a>'
            . '</main>'
            . '</body>'
            . '</html>';
    }
}
