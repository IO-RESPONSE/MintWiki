<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 제목이 비어있을 때 발생 (태스크 0401).
 *
 * Python `EmptyTitleError`(src/modules/document/title.py)와 안정적인
 * error code(`docs/portable-exception-code-policy.md`)를 맞춘다. 두 언어가
 * 반드시 같아야 하는 값은 CODE 문자열 하나뿐이며, 클래스 이름이나 메시지는
 * 자유롭게 짓는다.
 */
final class EmptyTitleError extends \Exception
{
    public const CODE = 'document.empty_title';
}
