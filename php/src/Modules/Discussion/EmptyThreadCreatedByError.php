<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 스레드 작성자 id가 비어있거나 공백만 있을 때 발생 (태스크 0410).
 *
 * Python `EmptyThreadCreatedByError`(src/modules/discussion/thread.py)에
 * 대응한다. EmptyThreadIdError와 같은 이유로 CODE 상수는 아직 두지 않는다.
 */
final class EmptyThreadCreatedByError extends \Exception
{
}
