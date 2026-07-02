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

DiscussionService/DiscussionRepository/감사 로그 등 나머지 계약은 이
태스크의 범위 밖이며 여전히 비어 있다.
