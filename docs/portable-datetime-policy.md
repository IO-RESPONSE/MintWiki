# Portable DateTime Policy

이 문서는 `datetime` 값의 저장 정책과 표시(display) 정책을 분리해 고정한다.
Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

`docs/service-method-contracts.md`(`BlockCheckService.is_blocked` 의
`now: datetime` 등)와 `docs/repository-port-contracts.md`, 그리고
`docs/persistence-boundaries.md` 의 `created_at`/`updated_at` 컬럼 정의는
이미 `datetime` 을 계약 타입으로 쓰고 있다. 이 문서는 그 값이 어떤 timezone
을 갖는지, 저장 시점과 표시 시점에 각각 무엇을 지켜야 하는지를 고정해
Python/PHP 양쪽 구현이 같은 규칙을 따르게 한다.

## 저장 정책: UTC 고정

- 도메인 계층(`service.py`/`model.py`)이 다루는 모든 `datetime` 값은 UTC
  timezone-aware 값이다. naive `datetime`(tzinfo 없음)은 도메인 계층
  경계를 넘지 않는다.
- 현재 시각이 필요한 서비스 코드는 `datetime.now(timezone.utc)` 만 쓴다.
  `datetime.now()`(로컬 서버 시각, naive)와 `datetime.utcnow()`(Python
  3.12 기준 deprecated, naive UTC를 반환)는 쓰지 않는다. 예:
  `DiscussionService.create_thread`(`src/modules/discussion/service.py`),
  `AclAuditRecorder.record`(`src/modules/acl/audit_recorder.py`) 모두
  `datetime.now(timezone.utc)` 를 쓴다.
- 데이터베이스 컬럼은 `docs/persistence-boundaries.md` 가 이미 고정한 대로
  timezone-aware 타입(`DateTime(timezone=True)`, SQL 표준 상 `DateTime(tz)`)
  으로 선언하고, 값은 UTC로 저장한다. 표시 timezone이나 UTC 오프셋을 별도
  컬럼에 함께 저장하지 않는다 — 저장 표현은 언제나 UTC 하나뿐이다.
- PHP 구현도 같은 규칙을 따른다: PHP `DateTimeImmutable` 값은 항상
  `new DateTimeZone('UTC')` 로 생성/변환한 뒤 저장하고, 서버의 기본
  timezone 설정(`date_default_timezone_set`)에 의존하지 않는다.

## 표시 정책: 저장과 표시의 분리

- 저장된 UTC 값은 그 자체로 표시용 문자열이 아니다. 사용자에게 보여줄
  시각은 UTC로 저장된 값을 표시 시점에 원하는 timezone으로 변환해서
  만든다 — 변환 결과를 저장소에 다시 쓰지 않는다.
- 표시 timezone은 도메인 계층이 아니라 어댑터 계층(HTTP 응답 포맷팅,
  향후 추가될 UI 렌더링 계층)의 책임이다. `service.py`/`model.py` 는
  표시 timezone을 인자로 받거나 알 필요가 없다 — `AGENTS.md` 의 이식성
  계층 규칙과 같은 이유로, 표시 형식(로케일, timezone 선택)은 프레임워크
  근접 관심사이기 때문이다.
- 이 문서를 작성하는 시점에는 표시 timezone을 사용자별로 선택하는 UI가
  아직 없다 — API 응답(`schema.py` DTO)은 UTC `datetime` 값을 ISO 8601
  형식으로 그대로 직렬화한다. 표시 timezone 변환 UI/설정은 이 문서의
  범위가 아니며, 도입될 때도 변환은 어댑터 계층에서만 일어난다는 이
  정책을 따라야 한다.
- 표시 변환은 항상 저장된 UTC 값을 원본으로 삼는다. 이미 변환된(로컬
  timezone이 반영된) 값을 다시 변환하거나, 변환된 값을 도메인 계층에
  되돌려 보내지 않는다.

## Wire 표현: ISO 8601 + UTC 오프셋

- 모듈 경계(서비스 메서드 입출력, API 응답, cross-language fixture)를
  넘어가는 `datetime` 값은 ISO 8601 형식이며 UTC 오프셋을 명시한다
  (`+00:00` 또는 `Z`). 오프셋 없는 문자열은 유효한 wire 값이 아니다.
- `docs/cross-language-fixture-schema.md` 의 fixture `input`/`expected`
  필드에 `datetime` 값을 담을 때도 이 형식을 그대로 쓴다. Python
  `datetime.isoformat()` 이 UTC-aware 값에 대해 만드는 `+00:00` 오프셋
  형식과, PHP `DateTimeImmutable::format(DATE_ATOM)` 이 만드는 형식이
  같은 문자열이 되도록 두 언어 모두 UTC 오프셋을 명시적으로 남긴다.
- 초 미만 정밀도(microsecond)는 wire 표현에서 고정하지 않는다 — fixture
  는 초 단위까지만 비교하거나, 필요하면 정밀도를 fixture 설명에 명시한다.

## 이 문서가 하지 않는 것

- 사용자별 표시 timezone을 선택/저장하는 기능을 설계하지 않는다. 이는
  UI가 추가되는 이후 단계(Phase 7 이후)의 범위다.
- 로케일별 날짜 포맷(`YYYY-MM-DD` vs `MM/DD/YYYY` 등) 문자열 포맷을
  정하지 않는다. 이 문서는 timezone 분리 원칙만 고정한다.
- 기존 코드에 새 필드나 변환 로직을 추가하지 않는다. 이 문서는 이미
  일관되게 지켜지고 있는 `datetime.now(timezone.utc)`/`DateTime(tz)`
  관행을 정책으로 고정할 뿐이다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 도메인 계층 프레임워크 결합 금지
  원칙과 PHP 전환 readiness gate.
- `docs/persistence-boundaries.md` — `created_at`/`updated_at` 컬럼의
  `DateTime(tz)` 타입 정의.
- `docs/service-method-contracts.md` — `datetime` 을 인자로 받는 서비스
  메서드 시그니처(`BlockCheckService.is_blocked` 등).
- `docs/repository-port-contracts.md` — 저장소 포트가 다루는 도메인 모델의
  `datetime` 필드.
- `docs/cross-language-fixture-schema.md` — `datetime` 값을 담는 fixture
  의 wire 형식.
- `docs/portability-glossary.md` — Contract/Adapter 용어 정의.
