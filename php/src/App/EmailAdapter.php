<?php

declare(strict_types=1);

namespace MintWiki\App;

/**
 * 이메일 발송 어댑터 계약.
 *
 * 실제 알림 흐름과 메일 전송 구현은 후속 태스크에서 연결한다.
 */
interface EmailAdapter
{
    public function send(string $recipient, string $subject, string $body): void;
}
