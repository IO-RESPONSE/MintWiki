# Jobs Polling Portable Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[Jobs Portable Repository Plan](jobs-portable-repository-plan.md) §7이 미뤄 둔
queued job polling/claim 정책을 확정한다.

## 목적

MintWiki의 최종 패키징 대상은 PHP + MariaDB shared hosting이다. 이 환경에서는
상시 워커, DB 전용 큐 기능, PostgreSQL 중심 락 문법을 기본값으로 둘 수 없다.
따라서 job polling은 다음 원칙을 따른다.

- 기본 경로는 MariaDB와 PostgreSQL 양쪽에서 표현 가능한 SQL만 사용한다.
- `SELECT ... FOR UPDATE SKIP LOCKED` 같은 전용 기능은 기본 구현에서 제외한다.
- shared hosting에서는 cron 또는 웹 트리거 job runner가 짧게 실행되고 종료된다.
- 동시 실행은 "claim update"의 영향 행 수(row count)로 판정한다.

## 후보 조회

poller는 실행 가능한 후보를 먼저 읽는다.

```sql
SELECT id
FROM job
WHERE status = 'queued'
  AND available_at <= ?
ORDER BY available_at, id
LIMIT ?
```

이 조회는 job을 claim하지 않는다. 여러 runner가 같은 후보를 볼 수 있으므로,
후보 조회 결과만으로 실행을 시작하면 안 된다.

## Claim Update

각 후보 id에 대해 runner는 조건부 `UPDATE`를 시도한다.

```sql
UPDATE job
SET status = 'running',
    attempts = attempts + 1,
    updated_at = ?
WHERE id = ?
  AND status = 'queued'
  AND available_at <= ?
```

영향 행 수가 `1`이면 해당 runner가 job을 claim한 것이다. 영향 행 수가 `0`이면
다른 runner가 먼저 claim했거나, 상태/시간 조건이 더 이상 맞지 않는 것이므로
그 후보는 건너뛴다.

이 방식은 `SKIP LOCKED` 없이도 중복 실행을 막는다. 핵심은 "읽기"가 아니라
상태 전이를 수행하는 `UPDATE`가 원자적이어야 한다는 점이다.

## 실패와 재시도

job 실행 실패 후 `attempts < max_attempts`이면 runner는 backoff을 계산해
다시 queued 상태로 되돌린다.

```sql
UPDATE job
SET status = 'queued',
    available_at = ?,
    last_error = ?,
    updated_at = ?
WHERE id = ?
  AND status = 'running'
```

`attempts >= max_attempts`이면 같은 행을 `dead_letter`로 전이한다. 별도
dead-letter 테이블은 만들지 않는다.

```sql
UPDATE job
SET status = 'dead_letter',
    last_error = ?,
    updated_at = ?
WHERE id = ?
  AND status = 'running'
```

성공 시에는 `succeeded`로 전이한다.

```sql
UPDATE job
SET status = 'succeeded',
    updated_at = ?
WHERE id = ?
  AND status = 'running'
```

## Stale Running 처리

shared hosting에서는 PHP 요청이 중간에 종료될 수 있다. runner는 일정 시간이
지난 `running` job을 운영자 진단 대상으로 표시해야 한다. 자동 재queue는 첫
구현 범위에서 제외한다. 자동 복구를 추가할 때도 다음 조건부 update를 사용한다.

```sql
UPDATE job
SET status = 'queued',
    available_at = ?,
    updated_at = ?
WHERE id = ?
  AND status = 'running'
  AND updated_at < ?
```

## 인덱스 후보

기본 schema에는 아직 인덱스를 추가하지 않는다. 실제 polling 구현이 들어가는
시점에 다음 인덱스를 추가한다.

- `ix_job_status_available_at_id` on `(status, available_at, id)`

이 인덱스는 후보 조회와 stale running 조회의 공통 필터를 지원한다.

## 금지 사항

기본 polling 구현은 아래 기능에 의존하지 않는다.

- `SKIP LOCKED`
- advisory lock
- DB vendor 전용 queue extension
- JSON/JSONB payload 조건 검색
- long-running daemon이 항상 떠 있다는 가정

## 관련 문서

- [Jobs Portable Repository Plan](jobs-portable-repository-plan.md)
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)
- [DB Web Hosting Constraints](db-web-hosting-constraints.md)
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md)
- [Shared Hosting Cron Policy](shared-hosting-cron-policy.md)
- [DB Phase QA Checklist](db-phase-qa-checklist.md)
