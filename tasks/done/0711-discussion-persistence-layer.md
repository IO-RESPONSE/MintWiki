# 0711 Discussion persistence layer

## Goal

토론(discussion) 기능의 **영속 계층**(저장소 + 서비스)을 신설한다 — 스레드/댓글을 DB에 읽고 쓴다. 라우트 배선(0712)의 전제.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Modules/Discussion (Repository 인터페이스 + PdoRepository + InMemoryRepository + Service)
- php/tests/Modules/Discussion, php/tests/Persistence

## Acceptance Criteria

- `Discussion\Repository` 인터페이스와 두 구현(`PdoRepository`, `InMemoryRepository`)을 추가한다. 최소 연산: 스레드 생성, 문서별 스레드 목록 조회, 스레드 단건 조회, 댓글 추가, 스레드별 댓글 목록 조회.
- `Discussion\Service`로 도메인 규칙(빈 본문/작성자 오류는 기존 `Empty*Error`, 스레드 상태 `ThreadState`)을 적용한 생성/조회 흐름을 제공한다.
- `PdoRepository`는 기존 스키마(`discussion_thread`, `discussion_comment`)에 매핑한다. `Revision\PdoRepository` 관례(생성 시 명시적 컬럼, 시간 내림/오름차순 정렬, 이식성 정책)를 따른다.
- 저장/조회 왕복이 SQLite(테스트)와 MariaDB(운영) 양쪽에서 동작하도록 이식성 정책을 지킨다(복합 인덱스/타임스탬프/정렬 tiebreaker).
- php 테스트로 `InMemoryRepository`와 `PdoRepository` 양쪽에 대해 스레드/댓글 CRUD 왕복, 정렬, 도메인 오류를 검증한다.

## Out of Scope

- HTTP 라우트·UI 배선(0712).
- 댓글 수정/삭제·중첩 답글 — 우선 생성/조회.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

현재 `Modules/Discussion`은 도메인 모델(`Thread`, `Comment`, `ThreadState`, `Empty*Error`)만 있고 **저장소·서비스가 없다**. 스키마 `db/schema/discussion_thread.sql`·`discussion_comment.sql` 존재. `Revision` 모듈의 `Repository`/`PdoRepository`/`InMemoryRepository` 구성을 템플릿으로. 도메인 프레임워크 금지, `MintWiki\Discussion` 네임스페이스, 도메인 모듈은 App/Http를 import하지 않는다(0424 규칙).
