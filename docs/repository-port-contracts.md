# Repository Port Contracts

이 문서는 각 모듈이 선언한 저장소 포트(repository ABC, `@abstractmethod` 로
정의된 추상 메서드)의 입력/출력/예외 계약을 고정한다. Phase A: PHP
Replacement Contract, 0351-0390 의 산출물이다.

이 문서는 **ORM 의존 없는 인터페이스 기준**으로 적는다 — 아래 각 메서드
시그니처는 도메인 모델(`Document`, `Revision` 등)과 원시 타입(`str`,
`int`, `Optional`, `list`)만 사용하며, `DocumentORM` 같은 SQLAlchemy 모델이나
`AsyncSession`, `select` 같은 SQLAlchemy 타입을 인자나 반환값으로 노출하지
않는다. `docs/portability-glossary.md` 의 **Port** 정의대로, 이 계약은
PHP 구현이 그대로 재현해야 하는 대상이다 — PHP 쪽은 ORM 을 아예 쓰지
않거나 다른 ORM 을 쓰더라도, 여기 적힌 메서드 이름·입력·출력·예외만
동일하면 같은 포트를 구현한 것으로 인정한다.

## 이 문서가 다루지 않는 것

- 서비스 메서드(`DocumentService.create` 등)의 계약은
  `docs/service-method-contracts.md` 가 담당한다. 그 문서의 시그니처에
  등장하는 저장소 타입은 참고용으로만 언급될 뿐, 이 문서가 정본이다.
- 개별 실패 사유의 error code 문자열(`document.not_found` 등)은
  `docs/portable-exception-code-policy.md` 가 담당한다. 이 문서는 어떤
  메서드가 어떤 예외 클래스를 던질 수 있는지만 고정한다.
- `InMemory*Repository`/`Database*Repository` 같은 구체 구현의 내부 동작,
  트랜잭션 경계, 데이터베이스 스키마는 `docs/persistence-boundaries.md` 가
  담당한다. 이 문서는 구현이 아니라 인터페이스(ABC)만 다룬다.
- `CacheBackend`(`src/modules/cache/backend.py`)와
  `SearchAdapter`(`src/modules/search/adapter.py`)는 구조적으로는 같은
  포트 패턴(ABC + `@abstractmethod`)을 따르지만, 클래스 이름이
  `Repository` 가 아니라 `Backend`/`Adapter` 다. 이 문서는 이름이
  `*Repository` 인 포트만 다루며, 두 클래스의 계약은 별도 문서의 범위다.
- 아직 `repository.py` 구현이 없는 모듈(admin, audit)은 이 문서에 싣지
  않는다. `admin` 은 0349(Add admin report repository interface),
  `audit` 는 0343(Add in-memory audit repository)이 실제 인터페이스를
  도입하면 이 문서를 갱신해 채운다.

## document (`src/modules/document/repository.py`, `DocumentRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `document: Document` | `Document` | `DuplicateNormalizedTitleError` |
| `get` | `id: str` | `Optional[Document]` | — |
| `get_by_normalized_title` | `normalized_title: str` | `Optional[Document]` | — |
| `update` | `document: Document` | `Document` | `DocumentNotFoundError` |

`create`/`update` 는 ABC docstring 상 "다양한 저장소 구현별 예외가 발생할
수 있음"이라고만 적혀 있지만, `InMemoryDocumentRepository` 와
`DatabaseDocumentRepository` 양쪽 구현이 실제로 던지는 예외는
`DuplicateNormalizedTitleError`(`document.duplicate_title`)와
`DocumentNotFoundError`(`document.not_found`) 두 가지뿐이다. 포트 계약은
이 두 예외를 안정적인 계약으로 고정한다.

## revision (`src/modules/revision/repository.py`, `RevisionRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `revision: Revision` | `Revision` | — |
| `get` | `id: str` | `Optional[Revision]` | — |
| `list_by_document_id` | `document_id: str` | `list[Revision]` (생성 순서) | — |

리비전은 append-only 이므로 `update`/`delete` 메서드가 없다 — 이는 누락이
아니라 `docs/persistence-boundaries.md` 가 고정한 불변성 규칙과 일치하는
의도된 계약이다.

## discussion (`src/modules/discussion/repository.py`, `DiscussionRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create_thread` | `thread: DiscussionThread` | `DiscussionThread` | — |
| `get_thread` | `id: str` | `Optional[DiscussionThread]` | — |
| `list_threads_by_document_id` | `document_id: str`, `limit: Optional[int] = None`, `offset: int = 0` | `list[DiscussionThread]` (생성 순서, limit/offset 적용) | — |
| `update_thread` | `thread: DiscussionThread` | `DiscussionThread` | `DiscussionThreadNotFoundError` |
| `create_comment` | `comment: DiscussionComment` | `DiscussionComment` | — |
| `list_comments_by_thread_id` | `thread_id: str`, `limit: Optional[int] = None`, `offset: int = 0` | `list[DiscussionComment]` (생성 순서, limit/offset 적용) | — |
| `get_comment` | `id: str` | `Optional[DiscussionComment]` | — |
| `update_comment` | `comment: DiscussionComment` | `DiscussionComment` | `DiscussionCommentNotFoundError` |

## user (`src/modules/user/repository.py`, `UserRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `user: User` | `User` | — |
| `get` | `id: str` | `Optional[User]` | — |
| `get_by_username` | `username: str` | `Optional[User]` | — |

## user 차단 (`src/modules/user/block_repository.py`, `BlockRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `block: Block` | `Block` | — |
| `get` | `id: str` | `Optional[Block]` | — |
| `get_by_user_id` | `user_id: str` | `Optional[Block]` | — |
| `delete` | `id: str` | `None` | — |

`user` 모듈은 계정용 `UserRepository` 와 차단용 `BlockRepository` 를 별도
포트로 분리한다 — 두 책임이 서로 다른 생명주기(계정은 update 없이 유지,
차단은 삭제로 해제)를 갖기 때문이다.

## user 세션 (`src/modules/user/session_repository.py`, `SessionRepository`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `session: Session` | `Session` | — |
| `get` | `id: str` | `Optional[Session]` | — |
| `delete` | `id: str` | `None` | — |

## 공통 패턴

- 조회 메서드(`get`, `get_by_*`)는 대상이 없으면 예외를 던지지 않고
  `Optional[T]` 로 `None` 을 반환한다. "없음"은 정상 결과이지 실패가
  아니다.
- 변경 메서드(`create`, `update`, `delete`)만 예외를 던질 수 있다. 존재를
  전제하는 `update`/`delete` 가 대상을 찾지 못하면 `*NotFoundError` 계열
  예외를 던진다.
- 목록 조회(`list_*`)는 생성 순서를 계약의 일부로 고정한다.
  `list_threads_by_document_id`/`list_comments_by_thread_id` 처럼
  `limit`/`offset` 을 받는 메서드는 페이지네이션도 계약에 포함된다.
- 어떤 메서드도 ORM 세션, 커넥션, 트랜잭션 객체를 인자로 받거나 반환하지
  않는다. `DatabaseDocumentRepository(session: AsyncSession)` 처럼 구현체의
  생성자가 세션을 받는 것은 허용되지만, 이는 인터페이스가 아니라
  구현 세부사항이다 — PHP 포트가 생성자에서 다른 방식(PDO, 커넥션 풀
  등)으로 의존성을 주입해도 포트 계약 위반이 아니다.

## 관련 문서

- `docs/php-replacement-strategy.md` — "PHP 구현은 Python 구현과 같은
  공개 메서드 이름·입력·출력 의미를 가져야 한다"는 원칙과 금지할 결합.
- `docs/service-method-contracts.md` — 서비스 계층 메서드 계약. 이 문서가
  고정한 저장소 포트를 호출하는 상위 계층이다.
- `docs/portable-exception-code-policy.md` — 이 문서가 나열한 예외
  클래스가 실어 날라야 하는 안정적 error code 정책.
- `docs/persistence-boundaries.md` — 이 문서가 다루지 않는 구체 구현
  (`InMemory*`/`Database*`)과 트랜잭션 경계.
- `docs/portability-glossary.md` — Port/Contract 용어 정의.
