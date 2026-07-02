<?php

declare(strict_types=1);

namespace MintWiki\Admin;

/**
 * 관리자 서비스 골격 (태스크 0414).
 *
 * admin 모듈은 Python 쪽에도 아직 어떤 구현 파일이 없다 —
 * `src/modules/admin`에는 README.md와 `manifest.json`만 존재하며,
 * `manifest.json`의 `service.public_methods`(block_user/unblock_user/
 * protect_page/unprotect_page/submit_report/resolve_report)와
 * `docs/service-method-contracts.md`의 admin 항목은 모두 이후 Python
 * 태스크(0345-0350, 아직 미실행)가 구현해야 할 목표 계약일 뿐이다.
 *
 * 그래서 이 클래스는 실제 비즈니스 로직을 옮긴 것이 아니라, manifest가
 * 이미 이름을 고정한 여섯 메서드를 block/protect/report 세 그룹으로 묶어
 * PHP 쪽에서 먼저 자리만 잡아 둔 것이다 — 입력/출력 타입, acl/user/
 * document/discussion/audit 의존성 연동, audit 기록 의무
 * (`src/modules/admin/manifest.json`의 audit hook 통과 의무 참고)는 모두
 * Python 구현이 확정된 뒤 별도 태스크에서 채워진다. 그때까지는 각
 * 메서드가 호출되면 `\LogicException`을 던져, 아직 구현되지 않은 자리임을
 * 명확히 알린다.
 */
final class Service
{
    private const NOT_IMPLEMENTED_MESSAGE = 'MintWiki\Admin\Service는 아직 골격만 있는 상태로, '
        . '실제 구현은 이후 태스크에서 채워진다.';

    /**
     * 사용자를 차단한다 (block 그룹, Python `block_user` 대응 placeholder).
     */
    public function blockUser(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }

    /**
     * 사용자 차단을 해제한다 (block 그룹, Python `unblock_user` 대응 placeholder).
     */
    public function unblockUser(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }

    /**
     * 문서를 보호한다 (protect 그룹, Python `protect_page` 대응 placeholder).
     */
    public function protectPage(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }

    /**
     * 문서 보호를 해제한다 (protect 그룹, Python `unprotect_page` 대응 placeholder).
     */
    public function unprotectPage(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }

    /**
     * 신고를 접수한다 (report 그룹, Python `submit_report` 대응 placeholder).
     */
    public function submitReport(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }

    /**
     * 신고를 처리 완료로 정리한다 (report 그룹, Python `resolve_report` 대응 placeholder).
     */
    public function resolveReport(mixed $payload = null): mixed
    {
        throw new \LogicException(self::NOT_IMPLEMENTED_MESSAGE);
    }
}
