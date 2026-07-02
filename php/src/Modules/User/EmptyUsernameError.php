<?php

declare(strict_types=1);

namespace MintWiki\User;

/**
 * 사용자명이 비어있거나 공백만 있을 때 발생 (태스크 0409).
 *
 * Python `EmptyUsernameError`(src/modules/user/model.py)에 대응한다.
 * Python 쪽에 아직 안정적인 error code(`code` 속성)가 없으므로
 * (`docs/portable-exception-code-policy.md`), 이 클래스도 CODE 상수 없이
 * 단순 예외로 둔다 — code 부여는 이후 태스크의 범위다.
 */
final class EmptyUsernameError extends \Exception
{
}
