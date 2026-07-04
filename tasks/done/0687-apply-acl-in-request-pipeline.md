# 0687 Apply ACL in request pipeline

## Goal

문서 읽기/쓰기 요청에 ACL 규칙을 적용해, 권한에 따라 허용/차단한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Modules/Acl
- php/tests

## Acceptance Criteria

- 문서 보기(0684)와 편집/저장(0685) 경로에 `Acl` 모듈을 적용해 현재 사용자(0686 세션)의 권한을 확인한다.
- 쓰기 권한이 없는 사용자의 편집/저장은 거부(403 또는 로그인 유도)한다.
- 읽기 전용/익명 사용자는 공개 문서를 읽을 수 있고, 보호된 문서 쓰기는 거부된다.
- 규칙 소스는 `acl_rule`/`acl_namespace_rule` 스키마와 기존 `Acl` 모듈을 사용한다.
- php 테스트로 관리자/일반/읽기전용/익명 각각의 읽기·쓰기 허용·거부를 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 세밀한 네임스페이스 관리 UI.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `src/Modules/Acl`, 스키마 `db/schema/acl_rule.sql`, `db/schema/acl_namespace_rule.sql`. 세션에서 사용자 식별은 0686 결과를 사용한다. 범위가 커지면 후속 큐 태스크로 분리한다.
