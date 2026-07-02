# Rate Limit Design

`user`/`acl` 모듈이 요청 빈도를 제한하는 방식에 대한 설계 노트. 아직 구현
태스크는 큐에 없으며, 이 문서는 로드맵의 **Phase 8: Hardening — rate limit
design** 항목을 위한 사전 설계 기록이다. 실제 rate limit 어댑터·미들웨어
구현은 이후 태스크에서 이 문서를 참조해 진행한다.

## 목적

익명/로그인 사용자가 짧은 시간에 과도한 요청(로그인 시도, 편집, 검색 등)을
보내는 것을 막아 브루트포스 공격과 자원 남용을 방지한다. `admin` 모듈의
[block](../src/modules/user/block.py) 이 "언제까지 차단"이라는 영구적·수동적
제재라면, rate limit은 "단위 시간당 N회"라는 자동적·일시적 제재다. 두 메커니즘은
서로 다른 계층에서 독립적으로 동작하며 하나가 다른 하나를 대체하지 않는다.

## 식별자: 기존 아이덴티티 모델 재사용

rate limit은 새로운 식별자 개념을 만들지 않고, `user` 모듈이 이미 가지고
있는 아이덴티티로 카운터 키를 구성한다.

- 로그인 사용자: user id (`modules.user.model`)
- 익명 방문자: [`IpIdentity`](../src/modules/user/ip_identity.py)의
  `ip_address`

`BlockCheckService`가 `user_id` 기준으로 차단 여부를 조회하는 것과 마찬가지로,
rate limit 카운터도 "로그인 사용자는 user id로, 익명은 IP로" 라는 동일한
구분을 따른다. 이렇게 하면 로그인 사용자가 IP를 바꿔도 우회할 수 없고,
익명 방문자 판별 로직을 두 번 만들지 않아도 된다.

## 도메인 모델 (엔진 비종속)

`search-adapter-design.md`와 동일한 원칙으로, 저장소·백엔드(인메모리 dict,
Redis 등)는 인터페이스 뒤에 숨긴다. 도메인 계층은 아래 값 객체만 다룬다.

```python
class RateLimitKey:
    """제한을 적용할 대상과 동작 종류를 함께 식별하는 키."""
    subject_id: str      # user id 또는 ip 주소
    action: str          # 예: "login_attempt", "edit", "search"


class RateLimitPolicy:
    """단위 시간당 허용 횟수."""
    max_count: int
    window_seconds: int


class RateLimitDecision:
    """단일 요청에 대한 판정 결과."""
    allowed: bool
    remaining: int
    retry_after_seconds: int
```

`RateLimitKey`에 `action`을 포함하는 이유: 로그인 시도와 일반 편집 요청은
허용 빈도가 크게 다르므로(로그인 시도는 엄격하게, 읽기 요청은 느슨하게)
동작별로 별도 카운터가 필요하다. 하나의 전역 카운터로 묶으면 정상적인 다독
사용자가 로그인 실패 시도자와 같은 한도를 공유하게 되어 오탐이 늘어난다.

## 어댑터 인터페이스 (포트)

```python
class RateLimiter(ABC):
    """카운터 저장소 포트. 인메모리·Redis 등 구현이 이 인터페이스를 만족한다."""

    @abstractmethod
    async def check(
        self, key: RateLimitKey, policy: RateLimitPolicy, now: datetime
    ) -> RateLimitDecision:
        """이번 요청을 허용할지 판단하고, 허용 시 카운터를 함께 증가시킨다."""
```

계약:

- `check`는 판정과 카운터 증가를 원자적으로 수행한다(판정만 하고 별도로
  증가시키는 2단계 API는 두지 않는다 — 동시 요청 사이의 경쟁 조건을 피하기
  위해서다).
- 윈도우가 지나면 카운터는 자동으로 리셋된다. 구현은 고정 윈도우(fixed
  window)든 슬라이딩 윈도우든 선택할 수 있으나, `RateLimitDecision`이
  반환하는 `retry_after_seconds`는 항상 "다음으로 허용될 때까지 남은 시간"을
  뜻해야 한다.
- 한도를 초과해도 예외를 던지지 않는다. 호출자가 `allowed`를 보고 429 응답
  여부를 결정한다. 카운터 저장소 접근 자체가 실패하는 경우(예: Redis 다운)는
  이 인터페이스의 책임이 아니라 구현체가 `cache` 모듈과 동일한 방식으로
  다룬다.

## 정책 소스: acl과의 관계

한도 값(`RateLimitPolicy`)은 `acl`의 그룹 개념을 재사용해 결정한다. 예를 들어
관리자 그룹은 더 높은 한도를, 신규/익명 사용자는 더 낮은 한도를 가질 수 있다.
그러나 이는 `acl`의 allow/deny 권한 판단과는 별개의 축이다:

- `acl`은 "이 동작을 **할 수 있는가**"를 판단한다.
- rate limit은 "이 동작을 **지금 얼마나 자주** 할 수 있는가"를 판단한다.

따라서 호출 순서는 항상 ACL 권한 검사가 먼저이고, 통과한 요청에 한해 rate
limit이 적용된다. 권한이 없는 요청은 애초에 카운터를 소모할 필요가 없다.

## 무엇을 인터페이스 밖에 두는가

- 카운터 저장 방식(인메모리 dict, Redis `INCR`+`EXPIRE`, SQL 테이블).
- 윈도우 알고리즘 선택(고정/슬라이딩/토큰 버킷).
- 동작별 실제 한도 수치(로그인 5회/분 같은 구체적인 숫자는 설정값이지
  인터페이스 계약이 아니다).
- 초과 시 사용자에게 보여줄 메시지·HTTP 응답 형식 (`router.py`의 책임).

## 이식 경로 (Python → PHP)

`search-adapter-design.md`와 동일한 패턴을 따른다: `RateLimitKey` /
`RateLimitPolicy` / `RateLimitDecision`은 값 객체이므로 PHP로 그대로
번역되고, `RateLimiter`는 PHP `interface`가 된다. 인메모리 구현은 테스트용으로
두 언어 모두에서 재사용 가능하며, 프로덕션 구현은 PHP 이식 시 MariaDB의
`INSERT ... ON DUPLICATE KEY UPDATE` 기반 카운터 테이블로 교체될 수 있다.
