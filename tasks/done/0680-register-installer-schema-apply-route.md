# 0680 Register installer schema apply route

## Goal

설치 마법사가 기록된 DB 설정으로 `db/schema/*.sql`을 적용해 위키 테이블을 생성하는 단계를 라우트로 등록한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Installer
- php/tests

## Acceptance Criteria

- `POST /install/schema`(및 진행 화면용 `GET`)가 `SchemaApply`를 사용해 `db/schema`의 SQL을 FK 의존 순서로 적용한다.
- 적용 대상 PDO는 0679가 기록한 설정을 0673 부트스트랩으로 읽어 만든다.
- 적용 성공 시 `schema_version`이 채워지고, 실패 시 오류를 표시하며 다음 단계로 넘어가지 않는다.
- CSRF 토큰을 검증한다.
- php 테스트로 스키마 적용 흐름(성공/실패)을 검증한다(실제 DB 없이 `SchemaApply`를 주입/모의 가능하게).
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 관리자 계정 생성 — 0681에서 수행.
- installer lock/완료 처리 — 0682.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Installer\SchemaApply`. FK 순서는 `db/schema` 및 기존 `scripts/mariadb_smoke_check.py`의 `SCHEMA_ORDER`를 참고한다. 스키마 파일은 배포 시 docroot 밖 `db/` 형제 디렉터리에 위치한다(경로 주입 가능하게).
