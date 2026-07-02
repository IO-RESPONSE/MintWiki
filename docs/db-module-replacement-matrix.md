# DB Module Replacement Matrix

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.

이 문서는 각 도메인 모듈이 데이터베이스 백엔드를 사용할 준비 상태를 **Python
repository** 구현과 **PHP PDO** 구현 두 축으로 추적한다. Python은 SQLAlchemy
기반 repository 패턴으로 postgres와 마리아DB를 모두 지원하도록 설계되었으며,
PHP는 PDO 드라이버를 통해 동일한 포트성 계약([db-adapter-contract.md](db-adapter-contract.md))을
만족해야 한다.

## 목적과 범위

- **목적**: 각 도메인 모듈(document, revision, user, acl, discussion, audit,
  jobs)이 어느 정도 DB 지원을 갖추었는지 한눈에 파악하기 위한 매트릭스.
- **추적 대상**:
  - Python: SQLAlchemy 기반 repository 패턴 구현 상태
  - PHP: PDO 어댑터 구현 상태
  - 각 단계의 정의는 다음 절에서 확정한다.
- **범위**: 이 문서는 현황 추적만 한다. 실제 구현은 후속 태스크에서 진행된다.

## 상태 정의

각 모듈-환경 조합에 대해 다음 상태 중 하나를 기록한다:

- **계획 단계** (`planned`): 포트 인터페이스와 도메인 모델은 정의되었으나,
  repository 구현은 아직 시작되지 않았다. 예: [User Portable Repository
  Plan](user-portable-repository-plan.md)(0454)이 정의했지만 실제 구현은
  아직이다.
- **진행 중** (`in-progress`): repository 구현이 활발하게 진행 중이거나,
  skeleton 구현이 완료되었다. 예: Document/Revision PHP skeleton (0487-0488).
- **표준 준수** (`standard-compliant`): 도메인 모듈 전체가 [DB Adapter
  Contract](db-adapter-contract.md)를 만족하는 완전한 repository 구현을
  갖춘 상태. 쿼리 기능, 트랜잭션 경계, 포트성 검증 모두 완료.
- **미정** (`not-started`): 아직 정의 단계도 진행되지 않은 상태.

## DB 모듈 상태 매트릭스

| 모듈 | Python Repository 상태 | PHP PDO 상태 | 비고 |
|---|---|---|---|
| **document** | 계획 단계 (0452) | 진행 중 (skeleton 0487) | 포트 가능 정책([portable-query-builder-policy.md](portable-query-builder-policy.md) 등) 정의 완료 |
| **revision** | 계획 단계 (0453) | 진행 중 (skeleton 0488) | 포트 가능 정책([portable-query-builder-policy.md](portable-query-builder-policy.md) 등) 정의 완료 |
| **user** | 계획 단계 (0454) | 미정 | [User Portable Repository Plan](user-portable-repository-plan.md) 정의 완료 |
| **acl** | 계획 단계 (0455) | 미정 | [ACL Portable Repository Plan](acl-portable-repository-plan.md) 정의 완료 |
| **discussion** | 계획 단계 (0456) | 미정 | [Discussion Portable Repository Plan](discussion-portable-repository-plan.md) 정의 완료 |
| **audit** | 계획 단계 (0457) | 미정 | [Audit Portable Repository Plan](audit-portable-repository-plan.md) 정의 완료 |
| **jobs** | 계획 단계 (0458) | 미정 | [Jobs Portable Repository Plan](jobs-portable-repository-plan.md) 정의 완료 |

## 관련 문서

### 계약과 정책
- [DB Adapter Contract](db-adapter-contract.md) — Python과 PHP 모두 만족해야 하는
  저장소 인터페이스 계약
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 포트 가능한
  SQL 제약 사항
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — 테이블과
  컬럼 명명 규칙

### 모듈별 계획 문서 (Python)

**계획 수립 완료:**
- [User Portable Repository Plan](user-portable-repository-plan.md) (0454)
- [ACL Portable Repository Plan](acl-portable-repository-plan.md) (0455)
- [Discussion Portable Repository Plan](discussion-portable-repository-plan.md) (0456)
- [Audit Portable Repository Plan](audit-portable-repository-plan.md) (0457)
- [Jobs Portable Repository Plan](jobs-portable-repository-plan.md) (0458)

**정책 정의 완료 (계획 문서는 후속):**
- Document, Revision: 포트 가능 정책 문서 참고
  ([portable-query-builder-policy.md](portable-query-builder-policy.md),
  [portable-id-column-policy.md](portable-id-column-policy.md),
  [portable-timestamp-column-policy.md](portable-timestamp-column-policy.md),
  [portable-text-collation-policy.md](portable-text-collation-policy.md))

### PHP 구현
- [PHP/README.md](../php/README.md) — PHP 디렉토리 구조 및 현황
- 실제 PHP repository 구현은 Phase C 0487 이후 태스크에서 진행된다.

### 인프라
- [Portable Migration Checklist](migration-portability-checklist.md) — 마이그레이션
  버전 관리 (schema_migration 테이블)
- [db/ README.md](../db/README.md) — portable SQL 원본 저장 위치

## 다음 단계

1. **Python repository 구현** (0450 이후): 각 모듈의 SQLAlchemy 기반
   repository 클래스 작성
2. **PHP skeleton 확대** (0487 이후): Document/Revision 이후 user, acl 등
   모듈로 PHP 구현 확대
3. **표준 준수 검증** (후속): 각 모듈이 db-adapter-contract.md를 완전히
   만족하는지 테스트
4. **마이그레이션 포트** (0460+): Alembic 마이그레이션을 db/ 아래 portable SQL로
   변환
