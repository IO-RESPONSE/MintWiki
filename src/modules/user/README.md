# user

Accounts and sessions.

Owns users, sessions, groups, credentials, and IP identity representation.

## User Identity Boundaries

Four "who is making this request" types live in this module. They share no
common base class or interface — each is a plain domain model with its own
fields, and the boundaries between them are easy to miss because nothing
enforces them at the type level.

### 1. `User` is the only identified type; it has no `is_anonymous` attribute

`User` (`model.py`) is constructed from an `id` and `username` and represents
an account that can log in. It does not define `is_anonymous` at all — not
even as `False`. `AnonymousIdentity` (`anonymous.py`) and `IpIdentity`
(`ip_identity.py`) both define `is_anonymous = True`. Code that needs to
branch on "is this an account or not" must use `getattr(x, "is_anonymous",
False)` (or an explicit `isinstance(x, User)` check); a plain `x.is_anonymous`
access raises `AttributeError` for a `User`. See
`test_anonymous.py::TestAnonymousIdentity::test_is_anonymous_flag_is_true` and
`test_ip_identity.py::TestIpIdentityConstruction::test_is_anonymous_flag_is_true`.

### 2. `AnonymousIdentity` vs `IpIdentity`: no identifier vs an IP identifier

Both represent a visitor who is not logged in, but they are not
interchangeable:

- `AnonymousIdentity` carries no identifying data at all. Every instance is
  equivalent except by object identity (`first is not second` in
  `test_anonymous.py`); it exists purely as a "not logged in" marker.
- `IpIdentity` carries a validated IP address (via `ipaddress.ip_address`,
  raising `InvalidIpAddressError` for a bad or empty value) and can therefore
  distinguish one anonymous visitor from another — e.g. for per-IP rate
  limiting or blocking. It is still permanently anonymous: it has no path to
  an account id and cannot become a `User`.

Neither type can hold a `User.id`, so neither can be swapped in wherever a
`user_id` string is expected (see point 4).

### 3. `AnonymousIdentity` and `IpIdentity` are not wired into ACL subject resolution

`SubjectType` (`modules/acl/rule.py`) has `USER`, `GROUP`, `ANONYMOUS`, and
`ALL` — there is no `SubjectType.IP`. `acl/router.py`'s `require_permission`
dependency does not construct or reference `AnonymousIdentity`/`IpIdentity`
at all: it reads a raw `Optional[str]` user id out of `request.state` and
maps its mere presence/absence directly to `SubjectType.USER` or
`SubjectType.ANONYMOUS`. No code path today extracts a request's IP address,
builds an `IpIdentity`, or feeds `ip_address` into a permission check — IP-based
ACL rules are not reachable through the current router even though the
domain model for one exists. See `modules/acl/router.py::require_permission`.

### 4. `Session`, `Block`, and `Group` only ever reference `User.id`

`Session.user_id`, `Block.user_id`, and `Group.member_ids` are all plain
user-id strings that presuppose a `User`. None of them accept an
`AnonymousIdentity`/`IpIdentity` instance, and nothing in this module
resolves an `IpIdentity` into a `Session`, `Block`, or `Group` membership. An
anonymous or IP-only visitor therefore cannot hold a session, cannot be
blocked via `BlockCheckService` (which requires a `user_id`), and cannot
belong to a group. This is why `acl/router.py` only calls
`block_check_service.is_blocked(...)` when a logged-in `user_id` is present —
there is no user id to check a block against otherwise.
