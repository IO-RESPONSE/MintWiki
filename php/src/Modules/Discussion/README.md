# php/src/Modules/Discussion

`MintWiki\Discussion` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.discussion` → PHP `MintWiki\Discussion`). 대응하는 계약
manifest 는 `src/modules/discussion/manifest.json` 이다.

## Thread/Comment/State 도메인 모델 (태스크 0410)

Python 쪽 `thread.py`/`comment.py`/`state.py` 세 모델을 1:1로 옮긴
도메인 모델이다. User/Decision과 달리 상태 전이 메서드가 있어 mutable
하다.

- `Thread` — 문서에 대한 토론 스레드. `id`/`documentId`/`title`/
  `createdBy`/`createdAt`/`status`(기본값 `'open'`)/`closedAt`/
  `pausedAt` 필드를 가진다. `title`은 주변 공백 제거 + 내부 공백을 단일
  공백으로 축소해 저장한다. `id`/`documentId`/`title`/`createdBy`가
  비어있거나 공백만 있으면 각각 `EmptyThreadIdError`/
  `EmptyThreadDocumentIdError`/`EmptyThreadTitleError`/
  `EmptyThreadCreatedByError`를 던진다. `close()`/`reopen()`/`pause()`는
  현재 상태와 무관하게 항상 성공하는 무조건 전이이며, `closedAt`/
  `pausedAt`은 서로 배타적이지 않다(`reopen()`만 `closedAt`을 지운다).
  `status`는 평범한 문자열이며 `ThreadState` enum으로 검증되지 않는다.
- `Comment` — 토론 스레드에 달린 댓글. `id`/`threadId`/`body`/
  `createdBy`/`createdAt`/`isHidden`(기본값 `false`)/`hiddenAt` 필드를
  가진다. `body`는 Thread의 `title`과 달리 정규화 없이 그대로 저장한다.
  네 id/text 필드가 비어있거나 공백만 있으면 각각
  `EmptyCommentIdError`/`EmptyCommentThreadIdError`/
  `EmptyCommentBodyError`/`EmptyCommentCreatedByError`를 던진다.
  `hide()`가 유일한 모더레이션 동작이며 멱등하게 재적용된다.
  `toPublicView()`/`toModeratorView()`는 Python dict 뷰와 맞춰 snake_case
  키(`thread_id`/`created_by`/`is_hidden`/`hidden_at`)를 쓰며, 전자만
  숨겨진 댓글의 `body`를 `null`로 가린다.
- `ThreadState` — `Open`/`Closed`/`Paused` 세 case를 가진 backed enum
  (`'open'`/`'closed'`/`'paused'`). Python `ThreadState`와 마찬가지로
  `Thread`가 참조하거나 검증에 쓰지 않는 독립된 타입이다.

`Empty*Error` 예외들은 아직 CODE 상수를 갖지 않는다 — 대응하는 Python
예외에 아직 `code` 속성이 없어서다(`docs/portable-exception-code-policy.md`).
code 부여는 discussion 모듈 error code 태스크와 0416(PHP error code
registry)의 범위다.

## Repository/Service (태스크 0711)

`Revision` 모듈의 `Repository`/`InMemoryRepository`/`PdoRepository`
구성을 템플릿으로 저장소·서비스를 추가했다. 최소 연산(스레드 생성/문서별
목록/단건 조회, 댓글 추가/스레드별 목록 조회) 다섯 개만 다룬다 — 라우트
배선(0712)의 전제다.

- `Repository` — `createThread`/`getThread`/`listThreadsByDocumentId`/
  `createComment`/`listCommentsByThreadId` 다섯 메서드만 선언한다. Python
  `DiscussionRepository`가 갖는 `update_thread`/`update_comment`/
  `get_comment`/limit·offset 페이지네이션은 댓글 수정·삭제·중첩 답글과
  함께 이 태스크 범위 밖이다.
- `InMemoryRepository` — id -> 엔티티 맵과 부모 id -> 자식 id 목록 맵을
  함께 유지해 문서별 스레드/스레드별 댓글을 생성 순서대로 조회한다.
- `PdoRepository` — `db/schema/discussion_thread.sql`/
  `discussion_comment.sql`을 그대로 사용한다. INSERT는 컬럼을 명시적으로
  나열하고, 목록 조회는 `created_at` 오름차순 + `id` 2차 정렬(tiebreaker)로
  정렬해 각 테이블의 복합 인덱스(`(document_id, created_at, id)`,
  `(thread_id, created_at, id)`)와 순서를 맞춘다. `created_at`/`closed_at`/
  `paused_at`/`hidden_at`은 애플리케이션이 UTC로 정규화한 문자열로
  저장/조회한다(`Acl\PdoRepository`의 `expires_at` 변환과 동일 방식).
- `Service` — `createThread`/`getThread`/`listThreadsByDocumentId`/
  `addComment`/`listCommentsByThreadId`만 옮긴다. 빈 본문/작성자 검증은
  새로 만들지 않고 `Thread`/`Comment` 생성자가 이미 던지는 `Empty*Error`에
  위임한다. 스레드 생성 시 초기 상태는 `ThreadState::Open`을 명시적으로
  전달한다. close/reopen/pause_thread, hide_comment, audit_recorder 연동은
  스레드 상태 전이·댓글 모더레이션이라 이 태스크 범위 밖이며 여전히
  비어 있다.
