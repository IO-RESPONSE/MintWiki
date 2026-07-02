# Codex Repository Rules

This repository is organized around small, explicit tasks that should fit in a
short runner cycle. Treat each task file as the source of truth for goal, scope,
acceptance criteria, out-of-scope items, and QA.

## 10-Minute Task Workflow

1. Read the assigned task completely before changing files.
2. Inspect the relevant existing files and follow current project patterns.
3. Make the narrowest change that satisfies the task acceptance criteria.
4. Add or update tests only when the task requires behavior that should be
   verified by tests.
5. Run the task's QA commands before finishing when possible.
6. Leave a concise final summary with what changed and which checks ran.

Complete exactly one task per runner cycle. Do not start the next queued task,
even if the current task is small or finishes quickly.

**`tasks/` 디렉토리는 절대 건드리지 않는다.** 태스크 파일을 생성·이동·이름변경·
삭제하지 않는다. 태스크 큐(queue/in-progress/done/failed 이동)는 러너가 전담한다.
에이전트가 `tasks/`를 손대면 러너가 깨진다.

## 언어 규칙 (Language)

- 코드 주석과 docstring은 **한글**로 작성한다.
- 커밋 메시지와 문서(README 등)는 **한글**로 작성한다.
- 단, 식별자(변수·함수·클래스·모듈명)와 코드 자체는 **영문**을 유지한다.

## 이식성 계층 규칙 (Portability Layering)

이 엔진은 **완성 후 백엔드를 모듈별로 PHP 로 전환**할 계획이다. 따라서 도메인
로직이 특정 웹 프레임워크·ORM·검증 라이브러리에 묶이지 않도록 계층 경계를
엄격히 지킨다. 새 코드를 작성할 때 반드시 아래 규칙을 따른다.

### 계층과 프레임워크 허용 범위

`src/modules/<모듈>/` 안에서 프레임워크 import 는 지정된 파일에만 둔다.

| 파일 | 역할 | 허용되는 프레임워크 |
|---|---|---|
| `router.py` | HTTP 어댑터 | `fastapi` / `starlette` 만 |
| `repository.py` | 영속성 어댑터 (+ 저장소 포트 인터페이스) | `sqlalchemy` 만 |
| `schema.py` | 요청/응답 DTO | `pydantic` 만 |
| `service.py`, `model.py`, 그 외 순수 로직 | **도메인 계층** | **없음 (금지)** |

- 도메인 계층(`service.py`/`model.py`/파서·렌더 등 순수 로직)은
  `fastapi` · `starlette` · `sqlalchemy` · `pydantic` · `asyncpg` · `uvicorn`
  · `alembic` 를 **절대 import 하지 않는다.** 이 계층은 표준 라이브러리와
  프로젝트 내부 모듈만 사용해 순수 Python 으로 유지한다.
- ORM 모델(`persistence/models.py`)과 도메인 모델(`modules/*/model.py`)은
  **분리**하고, 둘 사이는 `from_domain` / `to_domain` 매퍼로만 오간다. 도메인
  모델에 SQLAlchemy `Column` 등을 직접 달지 않는다.
- 저장소는 **포트(ABC 인터페이스) + 어댑터(구현)** 패턴을 유지한다. 서비스는
  구체 구현이 아니라 인터페이스에 의존한다.

### 실무 지침

- 검증 규칙 중 **형식 검증**(필수값·타입)은 `schema.py` 에, **비즈니스 규칙**
  (제목 정규화, 중복·권한 판단 등)은 도메인 계층에 둔다. 도메인 규칙을 Pydantic
  스키마에만 두지 않는다 (PHP 전환 시 함께 사라지기 때문).
- 정규식은 Python `re` 와 PHP PCRE 문법이 다를 수 있으므로, 정규식을 쓰는 순수
  로직 모듈은 입력→기대출력 픽스처 테스트를 촘촘히 유지한다.

### 자동 검사

이 경계는 `scripts/check_boundaries.py` 가 강제하며 `scripts/qa.sh` 에서 자동
실행된다. 위반 시 QA 가 실패하므로, 도메인 계층에 프레임워크를 끌어들이는 잡은
QA 를 통과할 수 없다.

## Scope Discipline

Do not implement work listed in a task's Out of Scope section. If an
out-of-scope item seems necessary, stop at the in-scope change and report the
constraint instead of expanding the task.

## Test and QA Commands

Use these repository-level checks:

```bash
scripts/test.sh
scripts/qa.sh
```

Run `scripts/test.sh` before finishing whenever possible. Run `scripts/qa.sh`
when the task requests full QA or before final handoff for changes that should
pass the repository quality gate.
