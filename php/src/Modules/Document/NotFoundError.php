<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * id로 문서를 찾을 수 없을 때 발생 (태스크 0402).
 *
 * Python `DocumentNotFoundError`(src/modules/document/repository.py)와
 * 안정적인 error code(`docs/portable-exception-code-policy.md`)를 맞춘다.
 * 클래스 이름은 `docs/php-namespace-mapping.md`가 고정한 규칙대로 이미
 * `MintWiki\Document` namespace 안에 있으므로 중복되는 `Document` 접두어를
 * 뺀다 (Python `DocumentService` -> PHP `MintWiki\Document\Service`와 동일한
 * 패턴).
 */
final class NotFoundError extends \Exception
{
    public const CODE = 'document.not_found';
}
