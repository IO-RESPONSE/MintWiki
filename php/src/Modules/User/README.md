# php/src/Modules/User

`MintWiki\User` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.user` → PHP `MintWiki\User`). 대응하는 계약
manifest 는 `src/modules/user/manifest.json` 이다.

## Identity value objects (태스크 0409)

Python 쪽 `anonymous.py`/`ip_identity.py`/`model.py` 세 모델을 1:1로
옮긴, 서로 독립된 세 identity value object다 — 공통 인터페이스는 두지
않는다(Python도 공통 베이스 클래스 없이 각자 `is_anonymous` 속성만
정의한다).

- `User` — 로그인한 사용자. `id`/`username`/`displayName`(선택) 필드를
  가지며, `isAnonymous` 속성이 없다. `username`이 비어있거나 공백만
  있으면 `EmptyUsernameError`를 던진다.
- `AnonymousIdentity` — 로그인하지 않은 방문자. 필드가 없으며
  `isAnonymous()`는 항상 `true`를 반환한다.
- `IpIdentity` — IP 주소만으로 식별되는 방문자. `ipAddress`(IPv4 또는
  IPv6) 필드를 가지며 `isAnonymous()`는 항상 `true`를 반환한다. 형식이
  올바르지 않은 IP 주소는 `InvalidIpAddressError`를 던진다.

`EmptyUsernameError`/`InvalidIpAddressError` 는 아직 CODE 상수를 갖지
않는다 — 대응하는 Python 예외(`model.py`/`ip_identity.py`)에 아직
`code` 속성이 없어서다(`docs/portable-exception-code-policy.md`). code
부여는 user 모듈 error code 태스크와 0416(PHP error code registry)의
범위다.

세션/그룹/차단/비밀번호 해셔 등 나머지 계약은 이 태스크의 범위 밖이며
여전히 비어 있다.
