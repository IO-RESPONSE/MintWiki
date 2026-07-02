# Portability Terminology Glossary

이 문서는 `docs/php-replacement-strategy.md` 가 정의한 PHP 전환 계약에서
반복적으로 쓰이는 이식성 관련 용어의 의미를 고정한다. 이후 태스크(manifest,
fixture, adapter 설계 등)는 여기 정의된 뜻으로만 용어를 사용해야 하며, 같은
단어를 문서마다 다른 의미로 쓰지 않는다.

Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

## Port

**Port** 는 하나의 언어 구현(Python)에서 다른 언어 구현(PHP)으로, 같은
모듈의 공개 동작을 옮기는 작업 단위를 가리킨다.

- 대상은 `src/modules/<module>` 디렉터리 하나이며, 앱 전체를 한 번에
  옮기는 것은 port 가 아니다(`docs/php-replacement-strategy.md` 의
  "모듈 단위 1:1 교체" 원칙 참고).
- port 의 결과물은 원본과 동일한 공개 서비스 메서드 이름·입력·출력
  의미를 가져야 한다. 내부 자료구조나 알고리즘은 언어별로 달라도 된다.
- port 가 "완료"되었다고 부르려면 해당 모듈의 parity fixture 테스트를
  새 언어 구현이 통과해야 한다.

## Adapter

**Adapter** 는 언어 독립 계약(contract)과 특정 언어/런타임의 구체
구현 사이를 잇는 얇은 경계 코드를 가리킨다.

- adapter 는 계약이 요구하는 입출력 형태를 그 언어의 관용적 형태로
  변환할 뿐, 새로운 비즈니스 규칙을 추가하지 않는다.
- adapter 는 도메인 계층(`service.py`/`model.py` 등)이 아니다. 프레임워크
  결합(예: HTTP 라우팅, DB 드라이버 특이 문법)은 adapter 층에만 있어야
  하며, `AGENTS.md` 의 이식성 계층 규칙이 금지하는 도메인 계층으로의
  누수를 막는 역할을 한다.
- Python 어댑터와 PHP 어댑터는 서로의 런타임을 호출하지 않는다. 공유하는
  것은 계약과 fixture 뿐이다.

## Contract

**Contract** 는 특정 언어 구현에 의존하지 않는, 모듈의 공개 동작에 대한
약속을 가리킨다. manifest, 서비스 메서드 시그니처, 에러 코드 목록,
fixture 를 합쳐 하나의 모듈 contract 를 이룬다.

- contract 는 코드보다 먼저 고정한다. 계약 없이 PHP 구현을 먼저 작성하지
  않는다(`docs/php-replacement-strategy.md` 참고).
- contract 에 선언되지 않은 내부 필드나 비공개 메서드에 다른 모듈이나
  adapter 가 직접 의존하는 것은 금지된 결합이다.
- contract 변경은 그 모듈에 관련된 모든 언어 구현과 fixture 를 함께
  갱신해야 한다.

## Fixture

**Fixture** 는 하나의 입력과 그에 대응하는 기대 출력을 언어 독립 형식
(JSON)으로 고정한 데이터를 가리킨다. Python 구현과 PHP 구현이 같은
fixture 를 입력으로 실행했을 때 같은 출력을 내야 parity 가 성립한다.

- fixture 는 모듈 contract 의 일부이며, 코드 저장소에서 두 언어가
  공유한다. 언어별로 별도의 fixture 를 만들지 않는다.
- 정규식처럼 언어마다 문법이 다를 수 있는 로직(제목 정규화 등)은 반드시
  fixture 로 입력/기대출력을 고정해 양쪽 구현을 맞춘다.
- fixture 는 parity 테스트(0387)와 readiness checklist(0388) 판단의
  근거 자료다. fixture 를 통과하지 못하면 해당 모듈은 전환 완료로 보지
  않는다.

## Shared Hosting

**Shared Hosting** 은 이 프로젝트가 PHP 전환의 배포 목표로 삼는, 사용자가
서버 프로세스나 런타임 버전을 직접 제어할 수 없는 공유 웹호스팅 환경을
가리킨다.

- shared hosting 환경은 별도 데몬 프로세스 상시 실행, 임의 포트 바인딩,
  커스텀 PHP 확장 설치를 전제할 수 없다고 가정한다.
- 기본 데이터베이스 경로는 ANSI SQL + MariaDB 호환을 우선한다
  (`docs/php-replacement-strategy.md` 의 PostgreSQL 전용 기능 금지 항목
  참고). PostgreSQL 전용 기능에 의존하는 설계는 shared hosting 목표와
  충돌한다.
- shared hosting 대상이라는 제약은 adapter 와 contract 설계 모두에
  적용된다: 배포 환경에서 재현 불가능한 가정(장기 실행 워커, 전용 포트
  등)을 계약에 넣지 않는다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 이 용어들이 쓰이는 전환 계약의
  배경 원칙.
- `docs/modules.md` — 모듈 책임과 의존 규칙.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — PHP 전환 큐 정책과
  Phase A/B 태스크 목록.
- `AGENTS.md` — 이식성 계층 규칙과 경계 검사.
