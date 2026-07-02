# php/src/Modules/Jobs

`MintWiki\Jobs` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었으며, 실제 구현은 이 모듈의 PHP 포팅이 진행되는 이후 태스크에서
채워진다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.jobs` → PHP `MintWiki\Jobs`). 대응하는 계약
manifest 는 `src/modules/jobs/manifest.json` 이다.

## 클래스

- `Runner.php` (0412) — jobs 모듈은 cache/document와 달리 Python 쪽에
  아직 어떤 구현 파일도 없어(`repository.py`/`service.py` 모두 미생성),
  기존 ABC를 옮기는 대신 `manifest.json`의 `service.public_methods`
  (`enqueue`/`run_sync`/`get_status`)를 PHP 쪽에서 먼저 계약으로 고정한
  포트 interface. `manifest.json`의 contract_notes가 명시하는 shared
  hosting 제약(큐 백엔드 없이도 `enqueue()`가 `runSync()`에 위임해
  요청/응답 사이클 안에서 동기적으로 처리를 끝낼 수 있어야 함)을
  반영한다. payload/결과/상태 타입은 `JobPayload`/`JobResult`/
  `JobStatus`가 아직 포팅되지 않아 `mixed`로 둔다. 잡을 영속화하는
  `JobRepository`(`manifest.json`의 `repository.interface`) 포트는
  메서드 시그니처가 아직 고정되어 있지 않아 이 태스크 범위 밖이며,
  이후 태스크에서 별도로 추가된다. 구현 없이 시그니처만 고정하며,
  Sync/Queued 등 구현체는 이후 태스크에서 추가된다.
