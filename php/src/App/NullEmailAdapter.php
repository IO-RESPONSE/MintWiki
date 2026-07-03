<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 이메일 발송을 비활성화한 기본 어댑터.
 *
 * 공유 호스팅 설치 직후에는 메일 설정이 없을 수 있으므로, 후속 알림 기능이
 * 실제 전송 어댑터를 연결하기 전까지 안전한 no-op 구현을 제공한다.
 */
final class NullEmailAdapter implements EmailAdapter
{
    public function send(string $recipient, string $subject, string $body): void
    {
    }
}
