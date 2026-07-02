# acl

Permission decisions.

Owns read, edit, discuss, move, delete, and admin permission checks. Protected
operations must call this module explicitly.

## ACL Evaluation Order

`AclService.check()` (`service.py`) resolves a single `Decision` for one
`(permission, subject_type, subject_id)` request in these steps, in order:

### 1. Resolve the rule list: document ACL fully overrides namespace defaults

`_resolve_rules()` picks exactly one source, never merges them:

- If a `DocumentAcl` is passed in and `document_acl.has_rules()` is true, its
  rules are used and namespace defaults are **not** consulted at all — even if
  none of the document's rules match the requested permission/subject. A
  document ACL that only restricts `EDIT` still causes `READ` checks on that
  document to fall through to "no matching rule" (default deny), not to the
  namespace's `READ` rule.
- Otherwise (no `DocumentAcl`, or one with an empty rule list), the
  `NamespaceAclDefaults` registered for the request's `namespace` are used. If
  no defaults were registered for that namespace, an empty list is used.

See `test_rule_precedence.py::TestDocumentAclFullyOverridesNamespaceDefaults`
and `test_service.py::TestAclServiceFallsBackToNamespaceDefaults`.

### 2. First matching rule wins, by registration order

The resolved rule list is scanned **in list order**. A rule is skipped unless
both are true:

- `rule.permission is permission` (exact match, no hierarchy between
  permissions).
- `rule.applies_to(subject_type, subject_id)` — `SubjectType.ALL` matches any
  subject; `USER`/`GROUP` require an exact `subject_id` match; `ANONYMOUS`
  matches only an anonymous request.

The **first** rule that matches both determines the `Decision` (its `effect`
becomes `allowed`, its `id` becomes `matched_rule_id`). There is no
"deny-overrides" or "most-specific-wins" logic — a broad `ALL` deny rule
placed before a narrow `USER` allow rule still wins, and vice versa. Callers
that assemble rule lists (e.g. `default_policy.py`) are responsible for
ordering more specific exceptions before the general rules they override. See
`test_rule_precedence.py::TestFirstMatchWinsRegardlessOfEffectCombination` and
`::TestOrderOverridesSpecificity`.

### 3. No match anywhere: deny by default

If nothing in the resolved rule list matches, `check()` returns a denied
`Decision` with `matched_rule_id=None` and `reason="no matching rule"`. This
is the fail-closed default for unregistered namespaces and for document ACLs
that don't cover the requested permission. See
`test_service.py::TestAclServiceWithoutRules`.

### 4. What `AclService.check()` deliberately does *not* evaluate

These are resolved by the caller before calling `check()`, not inside it:

- **Rule expiry.** `Rule.expires_at`/`Rule.is_expired(now)` exist on the
  domain model, but `check()` takes no `now` argument and never inspects
  expiry — it evaluates whatever rules it is handed as if all were active.
  Callers must filter out expired rules (via `Rule.is_expired`) before
  building the `DocumentAcl`/`NamespaceAclDefaults` passed in. See
  `test_expired_restriction.py`.
- **Group membership.** `check()` only compares the `subject_id` it is given
  against `GROUP` rules; it does not look up which groups a user belongs to.
  Callers must resolve membership via `Group.has_member(user_id)` first and
  then call `check()` once per candidate group id (falling back to `ALL` if
  no group rule matched). See `test_group_membership.py`.
- **User blocks.** Whether a user is currently blocked
  (`modules.user.block_check_service.BlockCheckService`) is checked by the
  `router.py` HTTP dependency (`require_permission`) **before** it calls
  `acl_service.check()`. A blocked user is rejected with 403 regardless of
  what the ACL rules say; the block check is not part of the ACL rule
  evaluation itself. See `test_blocked_user_cannot_edit.py`.
