# MintWiki 엔진 청사진

이 저장소는 새 위키 엔진 **MintWiki**의 설계·실행 스캐폴드입니다.
목표는 MediaWiki의 운영 아키텍처에서 영감을 받고, 나무위키(NamuWiki) 스타일의
사용자 워크플로우로 다듬은 모듈러·경량 엔진입니다.

프로젝트는 짧은 러너 사이클 안에서 구현·테스트·커밋할 수 있도록
작은 태스크 단위로 의도적으로 잘게 나뉘어 있습니다.

## 목표

- MediaWiki 플러그인이 아니라 새 위키 엔진을 만든다.
- 먼저 모듈러 모놀리스로 시작하되, 모듈 경계를 깨끗하게 유지한다.
- 개발 환경을 약 10분 안에 부트스트랩할 수 있게 한다.
- 모든 구현을 명시적 인수기준을 가진 작은 잡(job)으로 나눈다.
- 각 잡을 자동 QA로 독립 검증할 수 있게 한다.

## 현재 목표 스택

- 런타임: PHP 8.1+ (`php/`)
- 데이터베이스: MariaDB 호환 portable SQL (`db/schema/`)
- DB 접근: PDO 기반 persistence skeleton
- 설치/호스팅: shared hosting 배포를 목표로 한 installer/diagnostics 단계
- 참조 구현: Python + FastAPI 코어는 계약 검증용 reference로 유지
- 테스트: PHP framework-free smoke tests, Python portability/reference tests
- 배포: PHP + MariaDB 패키징 우선

## 로컬 환경

로컬 실행 전 `.env.example`을 `.env`로 복사한 뒤, PHP/MariaDB 환경에 맞게
DSN 값을 조정합니다.

### 부트스트랩

Docker Compose의 MariaDB 프로필로 로컬 DB를 기동합니다:

```bash
docker compose --profile mariadb up -d mariadb
```

### 테스트

PHP 런타임 테스트를 실행합니다:

```bash
cd php
composer install
scripts/qa.sh
```

### 커밋 전 QA

변경 사항을 점검하는 전체 로컬 QA 워크플로우를 실행합니다:

```bash
scripts/qa.sh
```

기본 QA는 PHP 런타임과 MariaDB portable SQL 산출물을 검증합니다. Python
reference 테스트까지 함께 실행하려면 `RUN_PYTHON_REFERENCE_QA=1 scripts/qa.sh`
를 사용합니다.

## 저장소 구조

```text
docs/              아키텍처 및 모듈 설계
db/                MariaDB 호환 portable SQL 원본
php/               PHP 런타임, installer, PDO persistence skeleton
tasks/             10분 잡 큐
src/app/           애플리케이션 부트스트랩 및 공용 설정
src/modules/       엔진 모듈
tests/             모듈 간 통합 테스트
scripts/           부트스트랩·테스트·QA·러너 헬퍼
ops/systemd/       systemd 서비스 및 타이머 예시
```

## 현재 상태

10분 잡 러너가 태스크 큐를 자동으로 소진하며, 아래 진행 현황은 **매 커밋마다
자동 갱신**됩니다.

<!-- PROGRESS:START -->
**진행률: 609 / 672 (90.6%)**

`█████████████████████████████████████████████░░░░░`

| 구분 | 개수 |
|---|---|
| ✅ 완료 | 609 |
| ⏳ 대기 | 63 |

- 갱신: 2026-07-03 15:29 KST
<!-- PROGRESS:END -->
