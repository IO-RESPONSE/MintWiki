-- user_session: 로그인 세션 테이블.
-- 스펙 원출처: src/modules/user/session.py의 Session,
-- src/modules/user/session_repository.py의 SessionRepository,
-- docs/user-portable-repository-plan.md §3.
--
-- 테이블 이름: Session 도메인 모델 자체가 아니라
-- user-portable-repository-plan.md §3이 확정한 `user_session`을 쓴다 —
-- 단일 단어 `session`은 [Portable Schema Naming Policy §5]가 나열한
-- 예약어 목록에는 없지만, 계획 문서가 account.sql(0463)과 동일하게
-- FK 대상 테이블 접두어(`user_`)를 붙여 이름 충돌 여지를 미리 없앤 결정을
-- 그대로 따른다.
--
-- account_id (user_id가 아님): account.sql(0463) 주석과
-- user-portable-repository-plan.md §2가 확정한 대로, account 테이블을
-- 참조하는 FK 컬럼은 `account_id`로 짓는다. Session 도메인 모델의
-- 필드명은 `user_id`이지만 저장 컬럼 이름은 스키마 네이밍 정책을
-- 우선한다 — 매핑은 이후 DatabaseSessionRepository 구현 태스크의 몫이다.
--
-- created_at/expires_at: [Portable Timestamp Column Policy §3]에 따라
-- 애플리케이션(서비스 계층)이 UTC로 정규화한 값을 INSERT 이전에 채워
-- 넣는다(server_default 없음) — Session.__init__이 이미 두 값을 필수
-- 인자로 받으므로 이 정책과 자연스럽게 맞는다. expires_at은
-- Session.is_expired(now)가 비교 기준으로 쓴다.
--
-- 인덱스: SessionRepository는 create/get/delete만 요구하고 셋 모두
-- id(PK) 기준이라 추가 인덱스가 필요 없다 — user-portable-repository-plan.md
-- §3의 판단을 그대로 따른다. account_id 조회(get_by_user_id류) 메서드가
-- 생기면 그 시점 태스크가 ix_user_session_account_id를 추가한다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / account_id: [Portable ID Column Policy]에 따라 애플리케이션이
--   생성한 UUID 문자열(VARCHAR(255))만 저장한다. PostgreSQL
--   SERIAL/gen_random_uuid(), MariaDB AUTO_INCREMENT/UUID() 어느 쪽도
--   쓰지 않으므로 두 DB에서 DDL이 동일하다.
-- - created_at / expires_at: [Portable Timestamp Column Policy]에 따라
--   애플리케이션이 이미 UTC로 정규화한 값을 넘기므로, PostgreSQL TIMESTAMP와
--   MariaDB TIMESTAMP 모두 그 값을 그대로 저장한다 — 두 DB에서 실제 저장
--   시각이 달라질 여지가 있는 지점은 세션 time_zone 설정뿐이며, 이는 DDL이
--   아니라 배포 설정으로 흡수한다(document.sql/revision.sql과 동일 판단).
--   MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지 않는다.
CREATE TABLE user_session (
    id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_user_session PRIMARY KEY (id),
    CONSTRAINT fk_user_session_account_id FOREIGN KEY (account_id) REFERENCES account (id)
);
