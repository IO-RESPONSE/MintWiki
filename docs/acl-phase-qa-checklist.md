# ACL Phase QA Checklist

로드맵 **Phase 4: ACL** (`docs/roadmap.md`) 범위 — user identities, groups,
document ACL rules, namespace defaults, permission matrix tests, protected
read/write paths — 가 회귀 없이 동작하는지 확인하기 위한 체크리스트다. 이
Phase에 속한 태스크를 새로 추가·수정한 뒤, 또는 커밋 전 `scripts/qa.sh`와는
별개로 ACL 동작 자체를 사람이 다시 훑어볼 때 사용한다.

각 항목은 "무엇을 확인하는가"와 "어떤 자동화 테스트가 이미 이를 커버하는가"를
함께 적는다. 자동화 테스트가 있다고 해서 항목을 건너뛰어도 된다는 뜻은
아니다 — 새 규칙/모듈을 추가할 때 아래 동작 각각이 여전히 성립하는지 의도를
가지고 재확인하라는 목적이다.

## 사용법

```bash
.venv/bin/python -m pytest tests/modules/acl tests/modules/user -v
```

위 명령으로 아래 체크리스트가 참조하는 테스트를 한 번에 실행할 수 있다.
개별 실행 후에는 반드시 `scripts/test.sh`와 `scripts/qa.sh`도 통과해야 한다.

## 1. User identities

- [ ] `User`는 `is_anonymous` 속성이 없고, `AnonymousIdentity`/`IpIdentity`는
      `is_anonymous = True`를 갖는다. See `test_model.py`,
      `test_anonymous.py::TestAnonymousIdentity`.
- [ ] `IpIdentity`는 유효하지 않은 IP 문자열에 대해
      `InvalidIpAddressError`를 던진다. See
      `test_ip_identity.py::TestIpIdentityConstruction`.
- [ ] `AnonymousIdentity`/`IpIdentity`는 `SubjectType.USER`/`GROUP`으로
      취급되지 않으며, `acl/router.py`의 `require_permission`은 로그인
      사용자 유무만으로 `USER`/`ANONYMOUS`를 결정한다. See
      `test_router.py::TestRequirePermissionAllowsAnonymous`,
      `src/modules/user/README.md` (User Identity Boundaries, 3항).

## 2. Groups

- [ ] `Group` 생성 시 멤버 목록이 격리되어, 한 그룹 인스턴스의 멤버 변경이
      다른 인스턴스에 영향을 주지 않는다. See
      `test_group.py::TestGroupConstruction`.
- [ ] `Group.has_member(user_id)`는 멤버십 변경(추가/제거) 이후 즉시 최신
      상태를 반영한다. See `test_group.py::TestGroupMembership`,
      `test_group_membership.py::TestMembershipChangesAffectDecision`.
- [ ] 한 사용자가 여러 그룹에 속할 때, 그 중 하나라도 허용 규칙과 매칭되면
      허용된다(그룹별로 개별 `check()` 호출이 필요하다는 전제 포함). See
      `test_group_membership.py::TestUserInMultipleGroups`.

## 3. Document ACL rules

- [ ] `DocumentAcl.has_rules()`가 참이면 네임스페이스 기본값은 전혀
      참조되지 않는다(부분 커버리지여도 폴백하지 않음). See
      `test_rule_precedence.py::TestDocumentAclFullyOverridesNamespaceDefaults`.
- [ ] 규칙 목록은 등록 순서대로 스캔되고, 조건에 맞는 첫 번째 규칙이
      승리한다 — effect 조합이나 규칙의 구체성과 무관하게. See
      `test_rule_precedence.py::TestFirstMatchWinsRegardlessOfEffectCombination`,
      `::TestOrderOverridesSpecificity`.
- [ ] 만료된(`is_expired`) 규칙은 `AclService.check()` 호출 전에 걸러지지
      않으면 여전히 활성 규칙처럼 평가된다 — 만료 필터링은 호출자 책임이다.
      See `test_expired_restriction.py`.
- [ ] `DocumentAcl.add_rule`/`remove_rule` 호출 시 `AclAuditRecorder`가
      규칙 추가/삭제 감사 이벤트를 정확히 하나 기록한다. See
      `test_audit_recorder.py`, `test_audit_event.py`.

## 4. Namespace defaults

- [ ] 문서 ACL이 없거나 규칙이 비어 있으면 등록된
      `NamespaceAclDefaults`로 폴백한다. See
      `test_service.py::TestAclServiceFallsBackToNamespaceDefaults`.
- [ ] 등록되지 않은 네임스페이스는 빈 규칙 목록으로 처리되어 기본
      거부(deny-by-default)로 귀결된다. See
      `test_namespace_defaults.py::TestNamespaceAclDefaultsFallback`.
- [ ] 네임스페이스 파서는 구분자가 없는 제목을 기본 네임스페이스로
      떨어뜨린다. See `test_namespace_parser.py::TestParseNamespaceFallsBackToDefault`,
      `test_namespace_fallback.py`.

## 5. Permission matrix

- [ ] `AclMatrixFixture`로 정의한 케이스가 `AclMatrixRunner`를 통해 전부
      실행되고, 실패한 케이스가 사람이 읽을 수 있는 형태로 보고된다. See
      `test_matrix_runner.py::TestAclMatrixRunnerFailures`.
- [ ] 기본 권한 매트릭스(그리드) 테스트가 read/edit/discuss/move/delete/
      admin 조합 전체에서 예상 결과와 일치한다. See
      `test_acl_matrix.py::TestAclMatrixBasicGrid`.

## 6. Protected read/write paths

- [ ] `require_read_permission`/`require_edit_permission` 의존성은 규칙이
      없을 때 기본적으로 거부하고, 익명 사용자가 허용 규칙과 매칭되면
      통과시킨다. See `test_require_read_permission.py`,
      `test_require_edit_permission.py::TestRequireEditPermissionAllowsAnonymous`.
- [ ] 차단된(`Block`) 사용자는 ACL 규칙상 허용되더라도 편집 경로에서
      403으로 거부되며, 차단은 ACL 규칙 평가와 별개 단계에서 이뤄진다. See
      `test_blocked_user_cannot_edit.py`,
      `test_require_edit_permission.py::TestRequireEditPermissionDeniesBlockedUser`,
      `src/modules/acl/README.md` (ACL Evaluation Order, 4항).
- [ ] 만료된 차단을 가진 사용자는 다시 편집할 수 있다. See
      `test_blocked_user_cannot_edit.py::TestFormerlyBlockedUserCanEditAfterExpiry`.

## 이 체크리스트가 다루지 않는 것

- rate limit 동작 — Phase 8 항목이며 `docs/rate-limit-design.md`에서 설계만
  다룬다.
- discussion 모듈의 ACL 연동 — Phase 5 항목이며 아직 큐에 있는 태스크
  (`add-discussion-acl-dependency-placeholder` 등)에서 다룬다.
- 실제 배포 환경에서의 성능/부하 특성 — 이 체크리스트는 기능적 정확성만
  다룬다.
