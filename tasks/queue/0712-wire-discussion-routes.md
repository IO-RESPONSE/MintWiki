# 0712 Wire discussion routes

## Goal

토론 라우트를 배선해 액션 탭의 "토론"이 실제로 동작하게 한다 — 문서별 스레드 목록/보기, 새 스레드 작성, 댓글 작성. 0711 영속 계층을 사용한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/public/index.php (discussion 라우트)
- php/src/Ui/DiscussionPage.php, php/src/Ui/CommentFormPage.php (데이터 주입)
- php/tests

## Acceptance Criteria

- `GET /wiki/{title}/discussion`을 등록한다 — 0711 서비스로 문서의 스레드(및 각 스레드 댓글)를 읽어 `DiscussionPage`로 렌더한다. 새 스레드 폼과 댓글 폼(`CommentFormPage`)을 포함한다.
- `POST /wiki/{title}/discussion`(새 스레드)과 `POST /wiki/{title}/discussion/{threadId}/comment`(댓글 추가)를 등록한다. 둘 다 `CsrfTokenService`로 검증(실패 403)하고, 저장 후 토론 페이지로 302 리다이렉트한다. 검증 오류는 폼에 재표시.
- ACL `discuss` 권한을 적용한다 — 읽기는 read, 쓰기(스레드/댓글)는 discuss 권한. 익명 쓰기 정책은 기존 edit 라우트 관례(비로그인 → /login 302)와 일관되게.
- 액션 탭의 "토론" 링크(`/wiki/{title}/discussion`)가 이제 200으로 동작한다. 스레드/댓글이 없을 때 빈 상태를 안전하게 렌더.
- 모든 입력/출력은 `Escaper`로 이스케이프하고 스킨 `Layout` 안에서 렌더한다.
- php 테스트로 (1) 토론 페이지가 스레드/댓글을 렌더, (2) 새 스레드·댓글 POST의 CSRF 거부와 정상 저장 후 리다이렉트, (3) ACL 거부, (4) 빈 상태를 검증한다.

## Out of Scope

- 댓글 수정/삭제, 스레드 잠금/해결 상태 전환 UI — 후속(모델의 ThreadState는 있으나 UI는 최소).
- 실시간 알림.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`DiscussionPage`·`CommentFormPage` 컴포넌트 존재, 0711에서 저장소·서비스 신설. ACL `Permission::Discuss` case 이미 있음. CSRF는 login/edit POST와 동일한 `Security\CsrfTokenService` 재사용.
