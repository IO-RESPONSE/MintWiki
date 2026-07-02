-- account: 사용자 계정 테이블.
-- 스펙 원출처: src/modules/user/model.py의 User,
-- docs/user-portable-repository-plan.md §2.
--
-- account/user 이름 결정: [Portable Schema Naming Policy §5]가 `user`를
-- PostgreSQL/MariaDB 예약어 충돌 위험 이름으로 지목해 `account`를 대체로
-- 제안했고, docs/user-portable-repository-plan.md §2가 이 테이블에 그
-- 대체를 적용하기로 확정했다 — 이 파일이 그 최종 확정이다. FK로 이
-- 테이블을 참조할 미래 컬럼(session, block 등)도 동일한 이유로
-- `account_id`를 쓴다(user_id가 아니다).
--
-- password/session 분리: 이 잡의 노트대로 비밀번호 해시와 세션은 이
-- 테이블에 두지 않는다. 비밀번호는 src/modules/user/password.py가
-- 다루는 별도 컬럼/테이블(번호 미배정)로, 세션은 user_session
-- 테이블(0464)로 분리한다.
--
-- created_at/updated_at 없음: User(model.py)가 이 필드를 갖지 않는다 —
-- document/revision과 달리 아직 DatabaseUserRepository도 Alembic
-- 마이그레이션도 없어(user-portable-repository-plan.md §1) 이 파일이
-- 옮길 스펙은 도메인 모델의 필드가 전부다. 추가가 필요해지면 그 시점
-- 태스크가 [Portable Timestamp Column Policy]에 따라 컬럼을 더한다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id: [Portable ID Column Policy]에 따라 애플리케이션이 생성한 UUID
--   문자열(VARCHAR(255))만 저장한다. PostgreSQL SERIAL/gen_random_uuid(),
--   MariaDB AUTO_INCREMENT/UUID() 어느 쪽도 쓰지 않으므로 두 DB에서 DDL이
--   동일하다.
-- - username: [Portable Text Collation Policy]에 따라 대소문자를
--   구분해서 비교해야 한다(tests/modules/user/test_repository.py의
--   test_username_lookup_is_case_sensitive). PostgreSQL은 기본 문자열
--   비교가 이미 바이트 단위 대소문자 구분이라 컬럼에 별도 지정이 필요
--   없지만, MariaDB 기본 collation(utf8mb4_general_ci 등)은 대소문자를
--   구분하지 않는다 — 이 차이는 document.sql(0461)과 동일하게 컬럼
--   정의가 아니라 MariaDB 쪽 서버/DB 문자셋 기본값을 utf8mb4_bin으로
--   맞추는 배포 설정으로 흡수한다(0512 이후 정해질 것이다).
CREATE TABLE account (
    id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NULL,
    CONSTRAINT pk_account PRIMARY KEY (id),
    CONSTRAINT uq_account_username UNIQUE (username)
);
