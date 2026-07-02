<?php

declare(strict_types=1);

/**
 * MintWiki\User\IpIdentity value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\User\InvalidIpAddressError;
use MintWiki\User\IpIdentity;

$failures = [];

$ipv4 = new IpIdentity('192.168.0.1');

if ($ipv4->ipAddress() !== '192.168.0.1') {
    $failures[] = 'ipAddress()가 생성자에 전달한 IPv4 값을 반환하지 않았다.';
}
if ($ipv4->isAnonymous() !== true) {
    $failures[] = 'isAnonymous()는 true를 반환해야 한다.';
}

$ipv6 = new IpIdentity('2001:db8::1');

if ($ipv6->ipAddress() !== '2001:db8::1') {
    $failures[] = 'ipAddress()가 생성자에 전달한 IPv6 값을 반환하지 않았다.';
}

$first = new IpIdentity('192.168.0.1');
$second = new IpIdentity('192.168.0.1');

if ($first === $second) {
    $failures[] = 'IpIdentity 인스턴스는 같은 IP라도 서로 다른 객체여야 한다.';
}

try {
    new IpIdentity('not-an-ip');
    $failures[] = '올바르지 않은 형식의 IP 주소는 InvalidIpAddressError를 던져야 한다.';
} catch (InvalidIpAddressError $e) {
    // 예상된 동작.
}

try {
    new IpIdentity('');
    $failures[] = '빈 문자열은 InvalidIpAddressError를 던져야 한다.';
} catch (InvalidIpAddressError $e) {
    // 예상된 동작.
}

if ($failures !== []) {
    fwrite(STDERR, "IpIdentity value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "IpIdentity value object 테스트 통과.\n");
exit(0);
