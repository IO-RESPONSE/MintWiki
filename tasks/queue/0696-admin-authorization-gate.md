# 0696 Admin authorization gate and first-admin grant

## Goal

관리자 전용 라우트를 보호할 재사용 가능한 **관리자 인가 게이트**를 만들고, 설치 마법사가 만든 최초 관리자 계정이 실제로 관리자 권한(`Permission::Admin`)을 갖도록 보장한다. 이 게이트는 이후 Phase I 태스크(0697+)가 각 관리자 화면 라우트에 공통으로 붙인다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/src/Http 또는 php/src/Security (AdminAccessGate/AdminGuard 등)
- php/src/Installer (AdminAccountSetupHandler — 최초 관리자 ACL 부여)
- php/tests

## Acceptance Criteria

- 현재 요청의 사용자가 관리자인지 판정하는 헬퍼를 추가한다. 판정은 기존 ACL을 재사용한다 — `AclService::check()`로 현재 subject(0687의 `SessionUserResolver`가 복원한 USER/ANONYMOUS)에 대해 `Permission::Admin`을 확인하고 `Decision::isAllowed()`로 결정한다. **account 테이블에 role/is_admin 컬럼을 추가하지 않는다**(권한은 ACL이 정본).
- 게이트는 세 가지 결과를 구분한다: (1) 비로그인 → `/login`으로 302, (2) 로그인했으나 관리자 아님 → 403, (3) 관리자 → 통과(null 반환 등으로 라우팅 계속). 기존 `InstallerRouteGate`의 `resolveFrontControllerResponse` 패턴과 일관되게 설계한다.
- 설치 마법사의 최초 관리자 생성(`AdminAccountSetupHandler`) 시 그 계정 id에 `Permission::Admin`을 부여하는 `acl_rule`을 함께 기록한다 — 그렇지 않으면 어떤 사용자도 관리자 게이트를 통과할 수 없다. 부여는 스키마/기존 ACL 저장소(`Acl\PdoRepository`) API로 하고, 이미 규칙이 있으면 중복 삽입하지 않는다.
- 게이트는 순수하게 인가만 담당하고 HTML을 만들지 않는다(차단 응답은 JSON 또는 기존 `ErrorPage`/`PermissionDeniedPage` 재사용).
- php 테스트로 세 경로(익명 302, 비관리자 403, 관리자 통과)와 최초 관리자 ACL 부여(중복 미삽입 포함)를 검증한다.

## Out of Scope

- 실제 관리자 화면 라우트 등록(0697+에서).
- 관리자 그룹/역할 관리 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `src/Modules/Acl/AclService.php`(`check()`→`Decision`), `Permission::Admin` case, `SubjectType::{User,Anonymous}`, `Acl\PdoRepository`(acl_rule/acl_namespace_rule 읽기). index.php는 이미 `resolveCurrentSubject()`류로 `[AclSubjectType, ?accountId]`를 만든다 — 게이트가 이를 재사용하도록 한다. `AdminAccountSetupHandler`는 계정 생성만 하고 ACL을 안 심는 공백이 있으니 이 태스크가 메운다. 관리자 부여 규칙의 subjectType은 `User`, subjectId는 생성된 계정 id, permission은 `admin`, 효과는 allow.
