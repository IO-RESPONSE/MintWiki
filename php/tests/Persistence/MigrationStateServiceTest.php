<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\MigrationStateService의 마이그레이션 상태 조회 기능을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\MigrationStateService;
use DateTimeImmutable;

$failures = [];

// 서비스 초기화 테스트
try {
    $service = new MigrationStateService();
    if ($service === null) {
        $failures[] = 'MigrationStateService 초기화가 실패했다.';
    }
} catch (Exception $e) {
    $failures[] = "MigrationStateService 초기화 실패: " . $e->getMessage();
}

$service = new MigrationStateService();

// 테스트용 SchemaVersion 모의 객체 생성 헬퍼
$createMockVersion = function (string $version, string $appliedAtStr): object {
    $obj = new stdClass();
    $obj->version = $version;
    $obj->applied_at = new DateTimeImmutable($appliedAtStr);
    return $obj;
};

// 현재 버전 조회: 빈 리스트
$result = $service->getCurrentVersion([]);
if ($result !== null) {
    $failures[] = '버전 목록이 비어있을 때 null을 반환해야 한다.';
}

// 현재 버전 조회: 단일 버전
$now = new DateTimeImmutable('2026-07-02T18:00:00+00:00');
$version = $createMockVersion('v1.0.0', '2026-07-02T18:00:00+00:00');
$result = $service->getCurrentVersion([$version]);

if ($result === null) {
    $failures[] = '단일 버전이 있을 때 null을 반환해서는 안 된다.';
} else {
    if ($result[0] !== 'v1.0.0') {
        $failures[] = '버전 문자열이 일치하지 않는다. 예상: v1.0.0, 실제: ' . $result[0];
    }
    if ($result[1] != $now) {
        $failures[] = 'applied_at이 일치하지 않는다.';
    }
}

// 현재 버전 조회: 여러 버전
$early = $createMockVersion('v1.0.0', '2026-07-01T18:00:00+00:00');
$middle = $createMockVersion('v1.1.0', '2026-07-02T18:00:00+00:00');
$latest = $createMockVersion('v1.2.0', '2026-07-02T19:00:00+00:00');

$result = $service->getCurrentVersion([$early, $middle, $latest]);

if ($result === null) {
    $failures[] = '여러 버전이 있을 때 null을 반환해서는 안 된다.';
} else {
    if ($result[0] !== 'v1.2.0') {
        $failures[] = '가장 최신 버전을 반환해야 한다. 예상: v1.2.0, 실제: ' . $result[0];
    }
    $latestTime = new DateTimeImmutable('2026-07-02T19:00:00+00:00');
    if ($result[1] != $latestTime) {
        $failures[] = '가장 최신 버전의 applied_at이 일치하지 않는다.';
    }
}

// 적용된 모든 버전 조회: 빈 리스트
$result = $service->getAppliedVersions([]);
if ($result !== []) {
    $failures[] = '버전 목록이 비어있을 때 빈 배열을 반환해야 한다. 실제: ' . json_encode($result);
}

// 적용된 모든 버전 조회: 정렬 확인
$v3 = $createMockVersion('v1.2.0', '2026-07-02T18:00:00+00:00');
$v1 = $createMockVersion('v1.0.0', '2026-07-02T18:00:00+00:00');
$v2 = $createMockVersion('v1.1.0', '2026-07-02T18:00:00+00:00');

$result = $service->getAppliedVersions([$v3, $v1, $v2]);
$expected = ['v1.0.0', 'v1.1.0', 'v1.2.0'];
if ($result !== $expected) {
    $failures[] = '버전이 정렬되지 않았다. 예상: ' . json_encode($expected) . ', 실제: ' . json_encode($result);
}

// 버전 적용 여부 확인: 적용된 버전
$versions = [
    $createMockVersion('v1.0.0', '2026-07-02T18:00:00+00:00'),
    $createMockVersion('v1.1.0', '2026-07-02T18:00:00+00:00'),
];

if (!$service->isVersionApplied($versions, 'v1.0.0')) {
    $failures[] = '적용된 버전 v1.0.0을 찾지 못했다.';
}
if (!$service->isVersionApplied($versions, 'v1.1.0')) {
    $failures[] = '적용된 버전 v1.1.0을 찾지 못했다.';
}

// 버전 적용 여부 확인: 미적용 버전
if ($service->isVersionApplied($versions, 'v1.2.0')) {
    $failures[] = '미적용 버전 v1.2.0을 적용된 것으로 잘못 판단했다.';
}
if ($service->isVersionApplied($versions, 'v2.0.0')) {
    $failures[] = '미적용 버전 v2.0.0을 적용된 것으로 잘못 판단했다.';
}

// 버전 적용 여부 확인: 빈 리스트
if ($service->isVersionApplied([], 'v1.0.0')) {
    $failures[] = '빈 리스트에서 항상 false를 반환해야 한다.';
}

// 버전 개수 조회: 빈 리스트
$result = $service->getVersionCount([]);
if ($result !== 0) {
    $failures[] = '버전 목록이 비어있을 때 0을 반환해야 한다. 실제: ' . $result;
}

// 버전 개수 조회: 여러 버전
$versions = [
    $createMockVersion('v1.0.0', '2026-07-02T18:00:00+00:00'),
    $createMockVersion('v1.1.0', '2026-07-02T18:00:00+00:00'),
    $createMockVersion('v1.2.0', '2026-07-02T18:00:00+00:00'),
];
$result = $service->getVersionCount($versions);
if ($result !== 3) {
    $failures[] = '버전 개수 조회 실패. 예상: 3, 실제: ' . $result;
}

// 버전 개수 조회: 단일 버전
$result = $service->getVersionCount([$createMockVersion('v1.0.0', '2026-07-02T18:00:00+00:00')]);
if ($result !== 1) {
    $failures[] = '단일 버전의 개수를 반환하지 못했다. 예상: 1, 실제: ' . $result;
}

if ($failures !== []) {
    fwrite(STDERR, "MigrationStateService 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "MigrationStateService 테스트 통과.\n");
exit(0);
