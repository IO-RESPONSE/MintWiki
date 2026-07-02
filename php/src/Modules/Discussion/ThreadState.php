<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 토론 스레드가 가질 수 있는 상태를 표현하는 enum (태스크 0410).
 *
 * Python `ThreadState`(src/modules/discussion/state.py)에 대응하며,
 * Thread::status()가 쓰는 문자열과 동일한 값을 가진다. Python 쪽과
 * 마찬가지로 Thread는 이 enum을 참조하거나 status를 이 enum으로
 * 검증하지 않는 독립된 타입이다(src/modules/discussion/manifest.json
 * 계약 노트) — 두 타입을 엮는 것은 이 태스크의 범위 밖이다.
 */
enum ThreadState: string
{
    case Open = 'open';
    case Closed = 'closed';
    case Paused = 'paused';
}
