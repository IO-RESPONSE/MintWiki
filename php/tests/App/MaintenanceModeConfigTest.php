<?php

declare(strict_types=1);

/**
 * MintWiki\App\MaintenanceModeConfig의 설정 기반 토글 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;
use MintWiki\App\MaintenanceModeConfig;

$failures = [];

$default = new MaintenanceModeConfig(new ConfigLoader([]));
if ($default->isEnabled() !== false) {
    $failures[] = 'maintenance_mode 설정이 없으면 기본값은 꺼짐이어야 한다.';
}

foreach (['1', 'true', 'yes', 'on', true, 1] as $enabledValue) {
    $config = new MaintenanceModeConfig(new ConfigLoader(['maintenance_mode' => $enabledValue]));
    if ($config->isEnabled() !== true) {
        $failures[] = 'maintenance_mode 값 ' . var_export($enabledValue, true) . '은 켜짐으로 해석되어야 한다.';
    }
}

foreach (['0', 'false', 'no', 'off', '', false, 0, 'unexpected'] as $disabledValue) {
    $config = new MaintenanceModeConfig(new ConfigLoader(['maintenance_mode' => $disabledValue]));
    if ($config->isEnabled() !== false) {
        $failures[] = 'maintenance_mode 값 ' . var_export($disabledValue, true) . '은 꺼짐으로 해석되어야 한다.';
    }
}

putenv('WIKI_MAINTENANCE_MODE=on');
$envConfigured = new MaintenanceModeConfig(new ConfigLoader(['maintenance_mode' => 'off']));
if ($envConfigured->isEnabled() !== true) {
    $failures[] = 'WIKI_MAINTENANCE_MODE 환경변수가 file-value보다 우선해야 한다.';
}
putenv('WIKI_MAINTENANCE_MODE');

if ($failures !== []) {
    fwrite(STDERR, "MaintenanceModeConfig 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "MaintenanceModeConfig 테스트 통과.\n");
exit(0);
