<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서 생성/조회 서비스 골격 (태스크 0403).
 *
 * Python `DocumentService`(src/modules/document/service.py)의 `create`/`get`
 * 계약만 옮긴다. `docs/service-method-contracts.md`의 document 섹션이 정본이며,
 * 나머지 공개 메서드(`get_by_title`, `get_current_revision_read_model`)는
 * revision 포트가 아직 PHP 쪽에 없어(0404/0405가 이후 추가) 이번 태스크
 * 범위에서 제외한다. 마찬가지로 `create`의 `source` 파라미터(첫 리비전 생성)
 * 도 revision 연동이 없는 지금은 다루지 않는다.
 *
 * 클래스 이름은 `docs/php-namespace-mapping.md`가 고정한 규칙대로 이미
 * `MintWiki\Document` namespace 안에 있으므로 중복되는 `Document` 접두어를
 * 뺀다 (Python `DocumentService` -> PHP `MintWiki\Document\Service`).
 */
final class Service
{
    public function __construct(private readonly Repository $documentRepository)
    {
    }

    /**
     * 새로운 문서를 생성한다.
     *
     * @throws EmptyTitleError title이 비어있거나 공백만 있는 경우
     * @throws DuplicateNormalizedTitleError normalizedTitle이 이미 존재하는 경우
     */
    public function create(string $title): Document
    {
        $document = new Document(self::generateId(), $title);

        return $this->documentRepository->create($document);
    }

    /**
     * 주어진 id로 문서를 조회한다. 없으면 null을 반환한다.
     */
    public function get(string $id): ?Document
    {
        return $this->documentRepository->get($id);
    }

    /**
     * UUID v4 문자열을 생성한다 (문서 id 발급용).
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
