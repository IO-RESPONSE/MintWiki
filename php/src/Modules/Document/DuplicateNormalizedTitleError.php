<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 정규화된 제목이 이미 존재할 때 발생 (태스크 0402).
 *
 * Python `DuplicateNormalizedTitleError`(src/modules/document/repository.py)와
 * 안정적인 error code(`docs/portable-exception-code-policy.md`)를 맞춘다. 두
 * 언어가 반드시 같아야 하는 값은 CODE 문자열 하나뿐이며, 클래스 이름이나
 * 메시지는 자유롭게 짓는다.
 */
final class DuplicateNormalizedTitleError extends \Exception
{
    public const CODE = 'document.duplicate_title';
}
