# Portable ID Policy

이 문서는 도메인 엔티티(`Document`, `Revision`, `DiscussionThread`,
`DiscussionComment`, `AclAuditEntry` 등)의 primary key `id` 값을 누가,
언제, 어떤 형식으로 생성하고 저장하는지 고정한다.
Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

`src/modules/document/service.py`, `src/modules/revision/service.py`,
`src/modules/discussion/service.py`, `src/modules/acl/audit_recorder.py`,
`src/modules/discussion/audit_recorder.py` 는 이미 모두 `id=str(uuid.uuid4())`
로 id 를 생성하고 있고, `docs/persistence-boundaries.md` 는 모든 `id`
컬럼을 `String(255) PRIMARY KEY` 로 고정하고 있다. 이 문서는 그 관행을
정책으로 고정해 Python/PHP 양쪽 구현과 PostgreSQL/MariaDB 양쪽 DB가 같은
규칙을 따르게 한다. DB 컬럼의 구체 타입/길이(ANSI SQL DDL)는
`docs/persistence-boundaries.md`(현재)와 이후 Phase C 의 "portable ID
column policy"(0444)가 다룬다 — 이 문서는 그 위에서 값이 어디서
생성되는지와 어떤 문자열 형식을 갖는지를 고정한다.

## 생성 정책: 애플리케이션 계층에서 생성

- `id` 값은 DB가 생성하지 않는다. `SERIAL`/`AUTO_INCREMENT`/
  `gen_random_uuid()`/DB native `UUID` 타입의 자동 생성 함수에 의존하지
  않는다. 값은 항상 도메인 계층(`service.py`) 또는 그 안에서 엔티티를
  만드는 코드가 저장 이전에 생성해서 채운다.
- 이렇게 하는 이유는 두 가지다. 첫째, PostgreSQL 과 MariaDB 는 native
  UUID 생성 함수와 컬럼 타입이 서로 다르다(`gen_random_uuid()` vs
  `UUID()`, `uuid` 타입 vs 없음) — id 생성을 DB 함수에 맡기면 두 DB가
  같은 스키마를 공유한다는 `docs/php-replacement-strategy.md` 의 전제가
  깨진다. 둘째, 도메인 계층이 저장 이전에 완성된 엔티티(id 포함)를
  만들 수 있어야 리포지토리 `create` 호출 전에 id 를 참조하는 코드
  (`docs/persistence-boundaries.md` 예제의 `document_to_create`/
  `revision_to_create` 처럼 서로를 참조하는 두 엔티티를 한 트랜잭션에서
  만드는 경우)가 성립한다.
- id 가 필요한 시점(엔티티 생성 시점)과 id 를 실제로 쓰는 시점(리포지토리
  `create` 호출) 사이에 DB 왕복이 없다 — 이는 정책의 결과이지 그 자체가
  목적은 아니다.

## 형식: UUID v4, canonical 36자 소문자 문자열

- id 는 RFC 4122 UUID version 4(무작위 생성)의 canonical 문자열 표현이다:
  소문자 16진수, 하이픈으로 구분된 8-4-4-4-12 자리, 총 36자
  (예: `3fa85f64-5717-4562-b3fc-2c963f66afa6`). 대문자, 중괄호(`{}`),
  URN 접두사(`urn:uuid:`)가 붙은 변형은 저장하지 않는다.
  Python `str(uuid.uuid4())` 가 만드는 문자열이 바로 이 형식이다.
- 모듈 경계(서비스 메서드 입출력, API 응답, cross-language fixture)를
  넘어가는 id 값도 같은 문자열 형식을 그대로 쓴다 — datetime 값과 달리
  (`docs/portable-datetime-policy.md` 참고) 저장 형식과 wire 형식 사이에
  변환이 없다. id 는 항상 하나의 문자열 표현만 갖는다.
- id 값 자체에 순서나 생성 시각 정보를 인코딩하지 않는다(순차 UUID,
  time-based UUID 등을 쓰지 않는다). 정렬이 필요한 목록은
  `created_at`(`docs/portable-datetime-policy.md`)이나 별도 컬럼으로
  정렬하고, id 는 식별자로만 쓴다.

## 저장 정책: 문자열 컬럼

- `docs/persistence-boundaries.md` 가 이미 고정한 대로 모든 `id` 컬럼은
  `String(255) PRIMARY KEY` 다. DB native `UUID` 컬럼 타입(PostgreSQL의
  `uuid`, 일부 MariaDB 확장의 `UUID`/`BINARY(16)` 압축 저장)은 쓰지
  않는다 — 36자 문자열 그대로 저장한다.
- 문자열로 저장하는 이유는 이식성이다: `BINARY(16)` 압축이나 PostgreSQL
  `uuid` 타입은 MariaDB/PostgreSQL 양쪽에서 동일하게 동작하지 않고,
  드라이버별 직렬화 규칙에 의존한다. 문자열 컬럼은 두 DB와 두 언어
  (Python `str`, PHP `string`) 모두에서 같은 바이트가 같은 값으로
  읽힌다.
- FK 컬럼(`revision.document_id`, `discussion_thread.document_id` 등)도
  참조 대상 `id` 와 같은 문자열 타입/길이를 쓴다 — id 를 참조하는 컬럼이
  참조 대상과 다른 표현을 갖지 않는다.

## PHP 구현 규칙

- PHP 구현도 id 를 애플리케이션 계층에서 생성하며, 위와 같은 canonical
  36자 소문자 UUID v4 문자열을 만든다. DB 함수나 프레임워크의 native
  UUID 컬럼 타입에 생성을 위임하지 않는다.
- PHP 쪽 UUID v4 생성에 쓸 구체 라이브러리(예: `ramsey/uuid`,
  `symfony/uid`, 또는 표준 확장만으로 구현)는 이 문서에서 고르지 않는다
  — Phase B(0391-0440) PHP 골격 태스크에서 결정한다. 이 문서가 고정하는
  것은 결과 문자열의 형식(canonical UUID v4)과 생성 위치(애플리케이션
  계층)뿐이다.

## 이 문서가 하지 않는 것

- id 컬럼의 SQL DDL(정확한 `VARCHAR` 길이, 인덱스 옵션 등)을 정하지
  않는다. 이는 `docs/persistence-boundaries.md`(이미 `String(255)`로
  고정)와 이후 Phase C 의 portable ID column policy(0444)의 범위다.
- PHP 쪽 UUID 생성 라이브러리를 선택하지 않는다.
- 기존 코드에 새 필드나 변환 로직을 추가하지 않는다. 이 문서는 이미
  일관되게 지켜지고 있는 `str(uuid.uuid4())` 관행을 정책으로 고정할
  뿐이다.
- UUID 가 아닌 다른 식별자 체계(자연 키, slug, 순번)를 도입하지 않는다.
  `Document.normalized_title` 같은 조회용 unique 컬럼은 이미 별도로
  존재하며 이 문서의 범위 밖이다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 두 언어가 같은 DB 스키마와
  fixture 를 공유해야 한다는 병행 기간 원칙.
- `docs/persistence-boundaries.md` — `id`/FK 컬럼의 `String(255)` 타입
  정의와 엔티티 생성 예제.
- `docs/service-method-contracts.md` — `id: str`/`*_id: str` 를 인자로
  받는 서비스 메서드 시그니처.
- `docs/repository-port-contracts.md` — 저장소 포트가 다루는 도메인
  모델의 `id` 필드.
- `docs/portable-datetime-policy.md` — 저장 형식과 wire 형식을 분리하는
  다른 값 타입(datetime) 정책과의 대비.
- `docs/portability-glossary.md` — Contract/Adapter 용어 정의.
