# ACL Fixtures

`modules.acl.service.AclService.check()` 가 반환하는 `Decision` 의
`allowed`/`reason`/`matched_rule_id` 결과 코드를 검증하는 교차언어
(cross-language) fixture다. 형식은
`docs/cross-language-fixture-schema.md` 가 고정한
`schema_version`/`input`/`expected`/`errors` 구조를 따른다.

`reason` 은 사람이 읽는 문장이 아니라 안정적인 code 문자열이다
(`docs/portable-exception-code-policy.md` 와 같은 `<module>.<reason>`
형식). `src/modules/acl/service.py` 의 `REASON_MATCHED_RULE`
(`"acl.matched_rule"`)과 `REASON_NO_MATCHING_RULE`
(`"acl.no_matching_rule"`) 두 값만 존재하며, 이 두 값이 fixture 로
고정된다. 이후 PHP 포트(0427 Add PHP ACL fixture parity tests)가 같은
fixture 를 재사용해 결과를 code 값으로만 비교한다.

규칙 우선순위(first-match-wins)나 그룹 소속 같은 나머지 매트릭스는 아직
Python 객체 형태의 `src/modules/acl/matrix_fixture.py`
(`AclMatrixFixtureLoader`)에만 있으며, 이 디렉터리는 `reason` code
자체를 고정하는 데만 쓰인다.

## 파일 목록

- `allow_when_matched_allow_rule.json` — ALLOW 규칙이 일치하면
  `allowed=true`, `reason=acl.matched_rule`.
- `deny_when_matched_deny_rule.json` — DENY 규칙이 일치해도
  `reason=acl.matched_rule` (규칙이 없어서가 아니라 규칙이 거부해서
  막힘).
- `deny_when_no_matching_rule_in_document_acl.json` — 문서 ACL은
  있지만 요청한 권한을 다루는 규칙이 없으면 네임스페이스 기본값을
  참조하지 않고 바로 `reason=acl.no_matching_rule`.
- `deny_when_no_rules_registered_anywhere.json` — 문서 ACL도 네임스페이스
  기본 규칙도 없는 골격 상태의 기본 거부 응답.
