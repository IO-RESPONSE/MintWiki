<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\I18n의 locale 관리와 번역 기능을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\I18n;

$failures = [];

// 기본 locale 테스트
$i18n = new I18n();
if ($i18n->getLocale() !== 'ko') {
    $failures[] = '기본 locale은 ko여야 한다.';
}

// locale 설정 테스트
$i18n->setLocale('en');
if ($i18n->getLocale() !== 'en') {
    $failures[] = 'setLocale()는 locale을 변경해야 한다.';
}

// locale을 다시 ko로 변경
$i18n->setLocale('ko');

// 생성자에 locale 지정 테스트
$i18nEn = new I18n('ja');
if ($i18nEn->getLocale() !== 'ja') {
    $failures[] = '생성자에서 locale을 지정할 수 있어야 한다.';
}

// t() 메서드 기본 동작 테스트
$i18n = new I18n();
if ($i18n->t('common.save') !== 'common.save') {
    $failures[] = 't() 메서드는 현재 key를 그대로 반환해야 한다.';
}

// parameter 치환 테스트
if ($i18n->t('common.hello_name', ['name' => 'World']) !== 'common.hello_name') {
    $failures[] = 't() 메서드는 key를 반환해야 한다.';
}

// parameter 치환이 있는 경우 테스트
if ($i18n->t('Hello :name', ['name' => 'World']) !== 'Hello World') {
    $failures[] = 't() 메서드는 :name 형식의 parameter를 치환해야 한다.';
}

// 다중 parameter 치환 테스트
if ($i18n->t('From :from to :to', ['from' => 'A', 'to' => 'B']) !== 'From A to B') {
    $failures[] = 't() 메서드는 여러 parameter를 치환해야 한다.';
}

// 빈 parameter 배열 테스트
if ($i18n->t('greeting.welcome', []) !== 'greeting.welcome') {
    $failures[] = 't() 메서드는 빈 배열로 호출되어도 동작해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "I18n 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "I18n 테스트 통과.\n");
exit(0);
