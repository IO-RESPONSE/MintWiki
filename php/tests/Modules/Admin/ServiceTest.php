<?php

declare(strict_types=1);

/**
 * MintWiki\Admin\Service 골격의 계약을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다 (0412 Jobs/RunnerTest.php와 동일한 방식).
 *
 * 태스크 0414는 실제 로직 없이 자리만 잡아 두므로, 이 테스트는 (1)
 * `src/modules/admin/manifest.json`이 고정한 여섯 개 공개 메서드
 * (block_user/unblock_user/protect_page/unprotect_page/submit_report/
 * resolve_report에 대응하는 blockUser/unblockUser/protectPage/
 * unprotectPage/submitReport/resolveReport)가 모두 존재하는지, (2) 각
 * 메서드를 호출하면 아직 구현되지 않았다는 `\LogicException`을 던지는지만
 * 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Admin\Service;

$failures = [];

if (!class_exists(Service::class)) {
    $failures[] = 'MintWiki\\Admin\\Service는 class여야 한다.';
}

$service = new Service();

$placeholderMethods = [
    'blockUser',
    'unblockUser',
    'protectPage',
    'unprotectPage',
    'submitReport',
    'resolveReport',
];

foreach ($placeholderMethods as $method) {
    if (!method_exists($service, $method)) {
        $failures[] = "Service에 {$method}() 메서드가 없다.";
        continue;
    }

    try {
        $service->{$method}(['dummy' => true]);
        $failures[] = "{$method}()는 아직 구현되지 않았으므로 \\LogicException을 던져야 한다.";
    } catch (\LogicException) {
        // 기대한 동작: 아직 구현되지 않은 자리라는 신호.
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Admin Service 골격 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Admin Service 골격 테스트 통과.\n");
exit(0);
