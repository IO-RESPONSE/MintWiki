# php/src/Modules/Cache

`MintWiki\Cache` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.cache` → PHP `MintWiki\Cache`). 대응하는 계약
manifest 는 `src/modules/cache/manifest.json` 이다.

- `Backend.php` (태스크 0411) — Python `CacheBackend`(src/modules/cache/backend.py)와
  대응하는 캐시 포트 interface. `get`/`set`/`delete` 기본 계약만 고정하며,
  Python 쪽의 `clear()`와 TTL/만료 정책, `RenderResult` 값 타입 결합은
  이 태스크의 범위 밖이다(값 타입은 `mixed`). 구현 없이 시그니처만
  고정하며, InMemory/Redis 등 구현체는 이후 태스크에서 채워진다.
