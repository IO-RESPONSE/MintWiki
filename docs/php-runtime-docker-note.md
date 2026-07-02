# PHP Runtime Docker Note

이 문서는 `php` CLI가 로컬 호스트에 설치되어 있지 않을 때, Docker
컨테이너로 `php/` 트리를 테스트하는 방법을 기록한다. Phase B: PHP
Runtime Skeleton, 0391-0440 의 산출물이다
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

## 목적: 로컬 테스트 편의, 배포 방식이 아니다

이 문서가 설명하는 Docker 사용은 **오직 로컬 개발 환경에서 `php` CLI를
쉽게 구하기 위한 편의 수단**이다. `docs/php-replacement-strategy.md`와
`docs/portability-glossary.md`("Shared Hosting")가 고정한 PHP 전환의
실제 배포 목표는 여전히 shared hosting이며, 이 문서는 그 목표를 바꾸지
않는다. 저장소 루트의 `Dockerfile`/`docker-compose.yml`은 기존 Python
앱(`app`, `postgres`, `redis` — `docs/architecture.md`)을 위한 것이고
PHP 런타임을 포함하지 않는다. 이 문서 역시 PHP용 `Dockerfile`이나
`docker-compose.yml` 서비스를 새로 추가하지 않는다.

## 로컬 테스트용 Docker 실행 예시

`php` CLI가 없는 개발 환경에서 공식 PHP 이미지를 컨테이너로 실행해
`php/` 트리의 테스트를 돌릴 수 있다. 예:

```sh
docker run --rm -v "$(pwd)/php:/app" -w /app php:8.1-cli \
  php tests/AutoloadSmokeTest.php
```

`scripts/test.sh`/`scripts/qa.sh` 전체를 컨테이너에서 돌리려면 같은
방식으로 볼륨을 마운트하고 스크립트를 실행한다:

```sh
docker run --rm -v "$(pwd)/php:/app" -w /app php:8.1-cli \
  ./scripts/test.sh
```

`composer install`이 필요하면 같은 컨테이너 안에서 먼저 실행한다
(`docs/php-test-bootstrap.md`). `php/composer.json`에 패키지 의존성이
없으므로 네트워크 접근 없이 끝난다.

## shared hosting과 Docker의 구분

- **shared hosting**은 이 프로젝트가 PHP 전환의 최종 배포 목표로 삼는
  환경이다 — 사용자가 서버 프로세스나 런타임 버전을 직접 제어할 수
  없고, 별도 데몬 상시 실행이나 임의 포트 바인딩, 커스텀 PHP 확장
  설치를 전제할 수 없다(`docs/portability-glossary.md`).
- **Docker**는 이 문서에서 오직 로컬 개발자가 `php` CLI를 설치하지
  않고도 테스트를 실행할 수 있게 해주는 도구일 뿐이며, PHP 코드의
  배포 대상이 아니다. Docker 컨테이너 안에서만 동작하는 가정(특정
  PHP 확장이 이미지에 사전 설치되어 있음 등)을 module contract나
  fixture에 넣지 않는다 — shared hosting에서 재현 가능해야 한다.
- 따라서 Docker로 테스트가 통과한다고 해서 shared hosting readiness
  gate(`docs/php-replacement-strategy.md`)를 만족한 것은 아니다. 두
  기준은 서로 다른 질문에 답한다: Docker는 "로컬에서 테스트를 어떻게
  돌리는가", shared hosting readiness는 "배포 대상 환경에서 실제로
  동작하는가"이다.

## 이 문서가 하지 않는 것

- PHP용 `Dockerfile`이나 `docker-compose.yml` 서비스를 추가하지
  않는다 — 이 문서는 순수 사용법 note다.
- 저장소 루트의 기존 `Dockerfile`/`docker-compose.yml`(Python 앱 전용)을
  수정하지 않는다.
- PHP 전환의 배포 목표를 shared hosting에서 Docker로 바꾸지 않는다.
- `php/scripts/test.sh`, `php/scripts/qa.sh`의 동작을 바꾸지 않는다 —
  이 문서는 같은 스크립트를 Docker 컨테이너 안에서 실행하는 방법만
  덧붙인다.

## 관련 문서

- `docs/php-replacement-strategy.md` — shared hosting 배포 목표와
  readiness gate의 배경.
- `docs/portability-glossary.md` — "Shared Hosting" 용어 정의.
- `docs/php-test-bootstrap.md` — `composer install` 및 `php` CLI로
  테스트를 실행하는 절차(로컬/컨테이너 공통).
- `docs/architecture.md` — 저장소 루트 Docker Compose(Python 앱 전용)
  구성.
- `php/README.md` — `php/` 트리 구조와 관련 문서 목록.
