# php/src/Modules/Audit

`MintWiki\Audit` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.audit` → PHP `MintWiki\Audit`). 대응하는 계약
manifest 는 `src/modules/audit/manifest.json` 이다.

## AuditEvent value object (태스크 0413)

`AuditEvent` — 중앙 audit 모듈이 기록하는 감사 이벤트를 표현하는 불변
value object다. `id`/`module`/`action`/`occurredAt`/`actorId`(선택)/
`metadata`(선택, 연관 배열) 필드를 가지며, `id`/`module`/`action`이
비어있거나 공백만 있으면 각각 `EmptyAuditEventIdError`/
`EmptyAuditEventModuleError`/`EmptyAuditEventActionError`를 던진다.

Python 쪽에는 아직 대응하는 audit 이벤트 모델이 없다 —
`src/modules/audit`에는 README.md와 manifest.json만 존재하며(태스크
0363), 이벤트 모델 구현 자체는 이후 Python 태스크(0342, 아직 큐에
있음)의 범위다. 그래서 이 클래스는 기존 Python 클래스의 1:1 포트가
아니라, `src/modules/audit/manifest.json`의 contract_notes가 이미
고정한 append-only 계약(record()가 유일한 쓰기 경로이며 한 번 기록된
이벤트는 수정·삭제될 수 없음)을 PHP value object 수준에서 먼저 굳힌
것이다 — 모든 필드를 readonly로 두고 mutator 메서드를 두지 않는
방식으로 표현한다.

acl/discussion 모듈이 이미 갖고 있는 자체 `AclAuditEvent`/
`DiscussionAuditEvent`(각 모듈 전용 action enum을 쓰는 별개 모델)는
이 클래스가 대체하지 않는다. module/action 필드를 문자열로 둔 것은
manifest가 audit의 책임으로 명시한 document/permission/admin/auth/job
로그를 모두 하나의 범용 이벤트로 담기 위해서다.

이벤트를 저장소에 append하는 서비스/저장소 포트(record/list_events)는
이 태스크의 범위 밖이며 이후 태스크가 채운다. `EmptyAuditEvent*Error`
세 클래스는 아직 CODE 상수를 갖지 않는다 — Python 쪽에 대응하는 error
code가 없어서다(`docs/portable-exception-code-policy.md`). code 부여는
0416(PHP error code registry)의 범위다.

## PdoAuditRecorder (태스크 0714)

`AuditRecorder`의 실제 PDO 구현체 — `audit_event` 테이블(`db/schema/audit_event.sql`)에
INSERT한다. 문서 생성/편집, 로그인 성공, 로그아웃이 이 recorder로 이벤트를
남긴다(`public/index.php`, `Security\LoginHandler`, `Security\LogoutHandler`).

`AuditEvent`의 `module`/`action`/`actorId`/`occurredAt`은 테이블 컬럼에 그대로
대응하지만, 테이블의 `entity_id`(NOT NULL)/`related_entity_id`(nullable)는
`AuditEvent`에 전용 필드가 없어 호출자가 `metadata`에 `entity_id`(필수)/
`related_entity_id`(선택) 키로 채워 넣는 관례로 전달한다. `entity_id`가 없으면
`MissingAuditEventEntityIdError`를 던지며, 호출자는 이 호출을 항상 try/catch로
감싸 감사 기록 실패가 사용자 요청을 깨뜨리지 않게 한다.
