<?php

declare(strict_types=1);

/**
 * MintWiki\Cache\Backend 포트의 시그니처와 계약을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0402 Document/RepositoryTest.php와
 * 동일한 방식).
 *
 * 태스크 0411은 구현 없이 port만 추가하므로, 이 테스트는 실제 캐시 백엔드
 * 동작이 아니라 (1) 인터페이스가 계약대로 구현 가능한지 — 익명 클래스로
 * 구현해 본다 — 와 (2) get/set/delete의 기본 동작만 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Cache\Backend;

$failures = [];

if (!interface_exists(Backend::class)) {
    $failures[] = 'MintWiki\\Cache\\Backend는 interface여야 한다.';
}

$backend = new class implements Backend {
    /** @var array<string, mixed> */
    private array $data = [];

    public function get(string $key): mixed
    {
        return $this->data[$key] ?? null;
    }

    public function set(string $key, mixed $value): void
    {
        $this->data[$key] = $value;
    }

    public function delete(string $key): void
    {
        unset($this->data[$key]);
    }
};

if ($backend->get('missing') !== null) {
    $failures[] = 'get()은 없는 key에 대해 null을 반환해야 한다.';
}

$backend->set('render:v1:abc', ['html' => '<p>Hello</p>']);
if ($backend->get('render:v1:abc') !== ['html' => '<p>Hello</p>']) {
    $failures[] = 'get()은 set()으로 저장한 값을 조회해야 한다.';
}

$backend->set('render:v1:abc', ['html' => '<p>Updated</p>']);
if ($backend->get('render:v1:abc') !== ['html' => '<p>Updated</p>']) {
    $failures[] = 'set()은 같은 key에 대해 값을 덮어써야 한다.';
}

$backend->delete('render:v1:abc');
if ($backend->get('render:v1:abc') !== null) {
    $failures[] = 'delete()는 저장된 key를 제거해야 한다.';
}

$backend->delete('never-set');

if ($failures !== []) {
    fwrite(STDERR, "Backend 포트 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Backend 포트 테스트 통과.\n");
exit(0);
