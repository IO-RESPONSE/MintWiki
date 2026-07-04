<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 문서 id가 비어있을 때 발생 (태스크 0687).
 *
 * Python `EmptyDocumentIdError`(src/modules/acl/document_acl.py)에 대응한다.
 */
final class EmptyDocumentIdError extends \Exception
{
}
