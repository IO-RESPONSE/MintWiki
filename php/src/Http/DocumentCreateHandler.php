<?php

declare(strict_types=1);

namespace MintWiki\Http;

use MintWiki\Audit\AuditRecorder;
use MintWiki\Audit\NoOpAuditRecorder;
use MintWiki\Audit\AuditEvent;
use MintWiki\Document\Service;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Security\IdempotencyKeyService;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\Escaper;

/**
 * POST /documents 요청을 처리하는 문서 생성 핸들러 (태스크 0531, 0569).
 *
 * 사용자가 제출한 title을 받아서 DocumentService.create()를 호출하고,
 * 성공 시 생성된 문서를 표시하고, 실패 시 에러 메시지를 반환한다.
 * 입력 데이터는 모두 escape되어 XSS를 방지한다.
 * Idempotency key를 검증하여 중복 제출을 방지한다 (태스크 0569).
 */
final class DocumentCreateHandler
{
    public function __construct(
        private readonly Service $documentService,
        private readonly IdempotencyKeyService $idempotencyKeyService = new IdempotencyKeyService(),
        private readonly DocumentViewPage $documentViewPage = new DocumentViewPage(),
        private readonly AuditRecorder $auditRecorder = new NoOpAuditRecorder()
    ) {
    }

    /**
     * 문서 생성 요청을 처리한다.
     *
     * @param string $title 사용자가 입력한 문서 제목
     * @param string $idempotencyKey 중복 제출 방지를 위한 idempotency key
     * @return Response 성공 시 생성된 문서, 실패 시 에러 메시지
     */
    public function handle(string $title, string $idempotencyKey = ''): Response
    {
        // Idempotency key 검증
        if (!$this->idempotencyKeyService->validate($idempotencyKey)) {
            return Response::html(
                $this->renderError('유효하지 않은 요청입니다.'),
                400
            );
        }

        try {
            $document = $this->documentService->create($title);

            // 감사 hook 호출
            try {
                $event = new AuditEvent(
                    id: self::generateId(),
                    module: 'document',
                    action: 'created',
                    occurredAt: new \DateTimeImmutable('now'),
                    actorId: null,
                    metadata: [
                        'document_id' => $document->id(),
                        'title' => $document->title()
                    ]
                );
                $this->auditRecorder->record($event);
            } catch (\Exception $e) {
                // 감사 기록 실패는 request 처리를 방해하지 않음
                \error_log('Audit recording failed: ' . $e->getMessage());
            }

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

    /**
     * UUID v4 문자열을 생성한다 (감사 이벤트 id 발급용).
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
}
