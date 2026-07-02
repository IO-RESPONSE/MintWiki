# php/src/Modules/Admin

`MintWiki\Admin` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.admin` → PHP `MintWiki\Admin`). 대응하는 계약
manifest 는 `src/modules/admin/manifest.json` 이다.

- `Service.php` (태스크 0414) — `manifest.json`의 `service.public_methods`
  (block_user/unblock_user/protect_page/unprotect_page/submit_report/
  resolve_report)를 block/protect/report 세 그룹으로 묶은 골격 클래스.
  Python 쪽 admin 구현이 아직 없으므로(태스크 0345-0350 미실행) 각
  메서드는 실제 로직 없이 `\LogicException`을 던지는 placeholder다.
