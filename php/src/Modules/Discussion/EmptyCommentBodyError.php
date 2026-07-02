<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 댓글 본문이 비어있거나 공백만 있을 때 발생 (태스크 0410).
 *
 * Python `EmptyCommentBodyError`(src/modules/discussion/comment.py)에
 * 대응한다. EmptyCommentIdError와 같은 이유로 CODE 상수는 아직 두지 않는다.
 */
final class EmptyCommentBodyError extends \Exception
{
}
