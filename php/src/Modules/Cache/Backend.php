<?php

declare(strict_types=1);

namespace MintWiki\Cache;

/**
 * 캐시 포트 (태스크 0411).
 *
 * Python `CacheBackend`(src/modules/cache/backend.py)와 대응하는 인터페이스.
 * `src/modules/cache/manifest.json`이 명시하듯 이 포트는 `Repository`가
 * 아니라 `Backend`로 명명되어 `docs/repository-port-contracts.md`의 범위
 * 밖이다 — 이 파일이 계약의 정본이다.
 *
 * 이 태스크는 노트대로 get/set/delete 기본 계약만 고정한다. Python 쪽의
 * `clear()`나 TTL/만료 정책은 포함하지 않으며, 값 타입도 아직 PHP로
 * 포팅되지 않은 `RenderResult`에 묶지 않고 `mixed`로 둔다. 구현 없이
 * 시그니처만 고정하며, InMemory/Redis 등 구현체는 이후 태스크에서
 * 추가된다.
 */
interface Backend
{
    public function get(string $key): mixed;

    public function set(string $key, mixed $value): void;

    public function delete(string $key): void;
}
