<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\RequirementCheck의 시스템 요구사항 검사 기능을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * PHP 확장 모듈 및 디렉터리 쓰기 권한을 검사하는 로직을 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\RequirementCheck;

$failures = [];

// RequirementCheck 초기화 테스트 - 기본 설정
try {
    $checker = new RequirementCheck();
    if ($checker === null) {
        $failures[] = 'RequirementCheck 초기화가 실패했다.';
    }
} catch (Exception $e) {
    $failures[] = "RequirementCheck 초기화 실패: " . $e->getMessage();
}

$checker = new RequirementCheck();

// 필수 확장 검사 - 정상 (기본 설정: pdo, json)
try {
    // pdo와 json은 대부분의 PHP 설치에 포함되어 있음
    if (!$checker->areRequiredExtensionsLoaded()) {
        $failures[] = '기본 필수 확장(pdo, json)이 있을 때 true를 반환해야 한다.';
    }
} catch (RuntimeException $e) {
    $failures[] = "기본 필수 확장 검사 실패: " . $e->getMessage();
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 필수 확장 검사 - 실패 (존재하지 않는 확장)
try {
    $checker = new RequirementCheck(['nonexistent_extension_xyz']);
    $checker->areRequiredExtensionsLoaded();
    $failures[] = '존재하지 않는 확장에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '필수 PHP 확장이 없습니다') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), 'nonexistent_extension_xyz') === false) {
        $failures[] = 'RuntimeException이 missing extension 이름을 포함해야 한다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 필수 확장 검사 - 실패 (여러 개의 존재하지 않는 확장)
try {
    $checker = new RequirementCheck(['ext1_notexist', 'ext2_notexist']);
    $checker->areRequiredExtensionsLoaded();
    $failures[] = '여러 개의 존재하지 않는 확장에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '필수 PHP 확장이 없습니다') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), 'ext1_notexist') === false || strpos($e->getMessage(), 'ext2_notexist') === false) {
        $failures[] = 'RuntimeException이 모든 missing extensions를 포함해야 한다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 디렉터리 쓰기 권한 검사 - 정상 (빈 목록)
try {
    $checker = new RequirementCheck(null, []);
    if (!$checker->areRequiredDirectoriesWritable()) {
        $failures[] = '필수 디렉터리가 없을 때 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "빈 디렉터리 목록 검사 실패: " . $e->getMessage();
}

// 디렉터리 쓰기 권한 검사 - 정상 (쓰기 가능한 디렉터리)
try {
    // /tmp는 일반적으로 쓰기 가능함
    $checker = new RequirementCheck(null, ['/tmp']);
    if (!$checker->areRequiredDirectoriesWritable()) {
        $failures[] = '/tmp는 일반적으로 쓰기 가능하므로 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "/tmp 디렉터리 검사 실패: " . $e->getMessage();
}

// 디렉터리 쓰기 권한 검사 - 실패 (존재하지 않는 디렉터리)
try {
    $checker = new RequirementCheck(null, ['/nonexistent_directory_xyz']);
    $checker->areRequiredDirectoriesWritable();
    $failures[] = '존재하지 않는 디렉터리에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '쓰기 불가능한 디렉터리가 있습니다') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), '/nonexistent_directory_xyz') === false) {
        $failures[] = 'RuntimeException이 nonexistent directory를 포함해야 한다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), '존재하지 않음') === false) {
        $failures[] = 'RuntimeException이 디렉터리가 존재하지 않는다는 이유를 포함해야 한다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 디렉터리 쓰기 권한 검사 - 실패 (쓰기 불가능한 디렉터리)
try {
    // /root는 일반적으로 쓰기 불가능하거나 접근 불가능함
    $checker = new RequirementCheck(null, ['/root']);
    $checker->areRequiredDirectoriesWritable();
    // /root가 존재하고 접근 가능한 경우를 위해 체크를 건너뜀
    // 대신 여러 디렉터리를 확인
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '쓰기 불가능한 디렉터리가 있습니다') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 디렉터리 쓰기 권한 검사 - 실패 (여러 개의 쓰기 불가능한 디렉터리)
try {
    $checker = new RequirementCheck(null, ['/nonexistent_dir1', '/nonexistent_dir2']);
    $checker->areRequiredDirectoriesWritable();
    $failures[] = '여러 개의 쓰기 불가능한 디렉터리에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '쓰기 불가능한 디렉터리가 있습니다') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// RequirementCheck에 커스텀 확장 목록을 전달할 수 있는지 확인
try {
    // 존재하는 확장과 존재하지 않는 확장을 섞어서 테스트
    $checker = new RequirementCheck(['pdo', 'json']);
    if (!$checker->areRequiredExtensionsLoaded()) {
        $failures[] = 'pdo와 json이 모두 있을 때 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "커스텀 확장 목록 테스트 실패: " . $e->getMessage();
}

// RequirementCheck에 커스텀 디렉터리 목록을 전달할 수 있는지 확인
try {
    $checker = new RequirementCheck(['pdo'], ['/tmp']);
    if (!$checker->areRequiredExtensionsLoaded()) {
        $failures[] = 'pdo가 있을 때 true를 반환해야 한다.';
    }
    if (!$checker->areRequiredDirectoriesWritable()) {
        $failures[] = '/tmp가 쓰기 가능할 때 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "커스텀 확장과 디렉터리 목록 테스트 실패: " . $e->getMessage();
}

$cacheDir = sys_get_temp_dir() . '/mintwiki_cache_check_' . getmypid();
if (!is_dir($cacheDir) && !mkdir($cacheDir, 0777, true)) {
    $failures[] = "cache 테스트 디렉터리를 만들 수 없다: {$cacheDir}";
}

if (is_dir($cacheDir)) {
    try {
        $checker = new RequirementCheck();
        if (!$checker->isCacheDirectoryWritable($cacheDir)) {
            $failures[] = 'cache 디렉터리가 쓰기 가능할 때 true를 반환해야 한다.';
        }
    } catch (Exception $e) {
        $failures[] = "cache 디렉터리 쓰기 가능 검사 실패: " . $e->getMessage();
    }

    if (!rmdir($cacheDir)) {
        $failures[] = "cache 테스트 디렉터리를 삭제할 수 없다: {$cacheDir}";
    }
}

// cache 디렉터리 쓰기 권한 검사 - 실패 (존재하지 않는 디렉터리)
try {
    $checker = new RequirementCheck();
    $checker->isCacheDirectoryWritable('/nonexistent_cache_directory_xyz');
    $failures[] = '존재하지 않는 cache 디렉터리에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    if (strpos($e->getMessage(), '쓰기 불가능한 디렉터리가 있습니다') === false) {
        $failures[] = 'cache RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), '/nonexistent_cache_directory_xyz') === false) {
        $failures[] = 'cache RuntimeException이 cache directory를 포함해야 한다: ' . $e->getMessage();
    }
    if (strpos($e->getMessage(), '존재하지 않음') === false) {
        $failures[] = 'cache RuntimeException이 디렉터리가 존재하지 않는다는 이유를 포함해야 한다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 테스트 결과 출력
if ($failures !== []) {
    fwrite(STDERR, "Installer RequirementCheck 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer RequirementCheck 테스트 통과.\n");
exit(0);
