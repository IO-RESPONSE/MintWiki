-- job: jobs 모듈(src/modules/jobs/)이 소유하는 background work
-- orchestration 테이블.
-- 스펙 원출처: src/modules/jobs/README.md(job interface, sync runner,
-- queued backend adapter, retry metadata, dead-letter handling),
-- docs/jobs-portable-repository-plan.md §3.
--
-- 테이블 이름: jobs_job처럼 모듈 접두어를 겹치지 않고 document/revision과
-- 같은 패턴으로 job 단수형 하나만 둔다 — jobs 모듈이 담는 개념이 모듈
-- 이름 자체와 같기 때문이다(jobs-portable-repository-plan.md §2). job은
-- PostgreSQL/MariaDB 예약어가 아니다.
--
-- status (CHECK 제약 없음, sync/queued 상태를 포함한다): sync runner가
-- 즉시 실행을 시작했다는 "sync", queued runner가 폴링할 "queued"를
-- 포함해 running/succeeded/failed/dead_letter까지 값 후보로 남긴다
-- (jobs-portable-repository-plan.md §4). 두 실행 모델을 위한 테이블을
-- 나누지 않고 이 컬럼 값만으로 흡수한다 — discussion_thread.status와
-- 동일한 이유로, 도메인 계층에 아직 Job 모델 자체가 없어(§1) CHECK
-- 제약을 걸지 않는다.
--
-- attempts / max_attempts / last_error (retry metadata): 지금까지 시도한
-- 횟수, 재시도 상한, 마지막 실패 원인을 각각 별도 컬럼으로 둔다.
-- attempts가 max_attempts에 도달하면 애플리케이션이 status를
-- dead_letter로 전이한다 — 별도 dead-letter 테이블은 두지 않는다
-- (jobs-portable-repository-plan.md §5).
--
-- available_at: queued runner가 폴링할 때 "지금 실행 가능한 job"을
-- 가리는 기준 시각. 재시도 backoff이 있으면 미래 시각을 저장한다.
--
-- payload (TEXT, 조건 검색 없음): JSON/JSONB 연산자는 MariaDB에
-- 대응물이 없어 금지 목록에 있으므로(ansi-sql-persistence-policy.md),
-- 애플리케이션이 직렬화한 문자열을 그대로 저장하고 payload에 대한 WHERE
-- 조건 검색은 전제하지 않는다.
--
-- updated_at을 둔다(audit_event와 다른 판단): job은 상태가 바뀌는 가변
-- 테이블이라 현재 상태만 담는다 — 상태 전이 이력은 이 테이블이 아니라
-- audit_event.category="job"이 맡는다(jobs-portable-repository-plan.md
-- §6).
--
-- FK 없음: job 테이블은 다른 도메인 테이블을 참조하는 컬럼을 두지
-- 않는다(jobs-portable-repository-plan.md §3).
--
-- locked_at/locked_by 같은 폴링 클레임 컬럼은 아직 두지 않는다 — 락/폴링
-- 메커니즘 자체가 이 태스크가 아니라 0516의 범위다
-- (jobs-portable-repository-plan.md §7).
--
-- 인덱스: 저장소 인터페이스 자체가 아직 없어 확립된 조회 패턴이 없다
-- (jobs-portable-repository-plan.md §8) — audit_event.sql과 동일한
-- 이유로 이 태스크에서는 인덱스를 추가하지 않는다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id: [Portable ID Column Policy]에 따라 애플리케이션이 생성한 UUID
--   문자열(VARCHAR(255))만 저장한다. 두 DB 모두 SERIAL/AUTO_INCREMENT/
--   UUID() 생성 함수를 쓰지 않으므로 DDL이 동일하다.
-- - available_at / created_at / updated_at: [Portable Timestamp Column
--   Policy]에 따라 애플리케이션이 UTC로 정규화한 값을 INSERT/UPDATE
--   이전에 채워 넣는다. PostgreSQL TIMESTAMP와 MariaDB TIMESTAMP 모두 그
--   값을 그대로 저장하며, MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지
--   않는다(다른 schema 파일과 동일 판단).
-- - job_type / status: [Portable Text Collation Policy]에 따라 고정된
--   소문자 문자열만 저장해 대소문자 비교 이슈가 없다 — 컬럼 정의에 별도
--   COLLATE 지정이 필요 없다(acl_rule.subject_type과 동일 근거).
CREATE TABLE job (
    id VARCHAR(255) NOT NULL,
    job_type VARCHAR(255) NOT NULL,
    payload TEXT NULL,
    status VARCHAR(20) NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL,
    available_at TIMESTAMP NOT NULL,
    last_error TEXT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_job PRIMARY KEY (id)
);
