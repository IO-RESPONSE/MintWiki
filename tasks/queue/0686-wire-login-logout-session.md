# 0686 Wire login, logout and session

## Goal

관리자/사용자 로그인·로그아웃과 세션을 연결한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/src/Modules/User
- php/src/Security
- php/tests

## Acceptance Criteria

- `GET /login`이 로그인 폼(아이디·비밀번호, CSRF 토큰)을 렌더한다.
- `POST /login`이 CSRF를 검증하고, `account` 테이블의 계정과 비밀번호 해시를 대조해 성공 시 세션을 시작한다(`PhpSessionAdapter`).
- `POST /logout`(또는 `GET /logout`)이 세션을 파기한다.
- 로그인 상태가 이후 요청에서 식별되도록 세션에서 현재 사용자/식별자를 복원한다.
- 실패한 로그인은 자격 증명을 노출하지 않고 폼으로 되돌린다.
- php 테스트로 로그인 성공/실패, 로그아웃, 세션 복원을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 문서별 ACL 적용 — 0687에서 수행.
- 비밀번호 재설정/회원가입 흐름.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Security\PhpSessionAdapter`, `MintWiki\Security\CsrfTokenService`, `MintWiki\Modules\User`. 계정 영속화는 0681이 추가한 계정 서비스/스키마(`account`)를 재사용한다.
