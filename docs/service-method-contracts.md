# Service Method Contracts

이 문서는 각 모듈의 `manifest.json` `service.public_methods` 가 이름만
나열한 공개 서비스 메서드에 대해, 실제 입력/출력 계약(파라미터 타입,
반환 타입, 발생 가능한 예외)을 고정한다. Phase A: PHP Replacement
Contract, 0351-0390 의 산출물이다.

이 문서는 **모듈별 public method** 만 다룬다 — 언더스코어로 시작하는
내부 헬퍼 메서드(`_resolve_rules` 등)나 아직 manifest 에 등재되지
않은 메서드는 계약 대상이 아니다. `docs/dto-naming-convention.md` 가
고정한 Request/Response DTO 이름 규칙, `docs/module-contract-manifest-schema.md`
가 고정한 manifest 스키마와 모순되지 않는다.

## 이 문서가 다루지 않는 것

- 저장소 포트(repository ABC)의 계약은 0378(Add repository port contract
  docs)이 담당한다. 이 문서의 서비스 메서드 시그니처에 등장하는 저장소
  타입(`DocumentRepository` 등)은 참고용으로만 언급한다.
- 개별 실패 사유의 error code 문자열 목록은 각 모듈의 error code
  태스크(0374 documnet 등, 아직 배정되지 않은 모듈은 이후 순번)가
  담당한다. 이 문서는 어떤 메서드가 예외를 던질 수 있는지와 그 예외
  클래스 이름만 고정한다.
- 서비스 메서드는 API 계층의 Request/Response DTO(`schema.py`)를 직접
  주고받지 않는다 — 대부분 원시 타입(`str`, `int`)이나 도메인 모델
  (`Document`, `Revision`, `DiscussionThread` 등)을 주고받으며,
  Request/Response 변환은 라우터(`router.py`) 계층의 책임이다. 이 문서는
  서비스 계층 시그니처만 고정하며, `docs/dto-naming-convention.md` 가
  고정한 API 계층 DTO 계약과는 별개다.
- 아직 Python 구현이 없는 모듈(admin, audit, jobs)은 manifest 가 선언한
  메서드 이름만 계약으로 옮겨 적고, 실제 시그니처는 구현 태스크가
  확정될 때 이 문서를 갱신한다.

## document (`src/modules/document/service.py`, `DocumentService`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `title: str`, `source: Optional[str] = None` | `Document` | `EmptyTitleError`, `DuplicateNormalizedTitleError` |
| `get` | `id: str` | `Optional[Document]` | — |
| `get_by_title` | `title: str` | `Optional[Document]` | `EmptyTitleError` |
| `get_current_revision_read_model` | `document_id: str` | `Optional[CurrentRevisionReadModel]` | — |

`CurrentRevisionReadModel` 은 `docs/dto-naming-convention.md` 가 정의한
ReadModel 역할의 예시이며, `document.service` 안에 선언된 내부 조회
전용 구조체다.

## revision (`src/modules/revision/service.py`, `RevisionService`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create` | `document_id: str`, `source: str`, `author_id: str`, `summary: str`, `parent_revision_id: Optional[str] = None` | `Revision` | — |
| `get` | `id: str` | `Optional[Revision]` | — |
| `list_by_document_id` | `document_id: str` | `list[Revision]` (생성 순서) | — |

## discussion (`src/modules/discussion/service.py`, `DiscussionService`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `create_thread` | `document_id: str`, `title: str`, `created_by: str` | `DiscussionThread` | — |
| `get_thread` | `id: str` | `Optional[DiscussionThread]` | — |
| `list_threads_by_document_id` | `document_id: str`, `limit: Optional[int] = None`, `offset: int = 0` | `list[DiscussionThread]` (생성 순서) | — |
| `close_thread` | `thread_id: str` | `DiscussionThread` | `DiscussionThreadNotFoundError` |
| `reopen_thread` | `thread_id: str` | `DiscussionThread` | `DiscussionThreadNotFoundError` |
| `pause_thread` | `thread_id: str` | `DiscussionThread` | `DiscussionThreadNotFoundError` |
| `add_comment` | `thread_id: str`, `body: str`, `created_by: str` | `DiscussionComment` | — |
| `list_comments_by_thread_id` | `thread_id: str`, `limit: Optional[int] = None`, `offset: int = 0` | `list[DiscussionComment]` (생성 순서) | — |
| `hide_comment` | `comment_id: str`, `actor_id: Optional[str] = None` | `DiscussionComment` | `DiscussionCommentNotFoundError` |

`create_thread` 와 `hide_comment` 는 성공 시 `DiscussionAuditRecorder` 로
감사 이벤트도 함께 남기지만, 이는 부수 효과이며 반환값 계약에는 포함되지
않는다.

## acl (`src/modules/acl/service.py`, `AclService`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `check` | `permission: Permission`, `subject_type: SubjectType`, `subject_id: Optional[str] = None`, `document_acl: Optional[DocumentAcl] = None`, `namespace: str = DEFAULT_NAMESPACE` | `Decision` | — |

`check` 은 예외를 던지지 않는다 — 일치하는 규칙이 없으면 `Decision.allowed
= False`, `Decision.reason = REASON_NO_MATCHING_RULE`
(`"acl.no_matching_rule"`)를 반환해 안전하게 거부하는 것이 계약의 일부다.
규칙이 일치하면 `reason = REASON_MATCHED_RULE`(`"acl.matched_rule"`)이고
`matched_rule_id` 로 근거 규칙을 알 수 있다.

## user (`src/modules/user/block_check_service.py`, `BlockCheckService`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `is_blocked` | `user_id: str`, `now: datetime` | `bool` | — |

`user` 모듈의 나머지 책임(계정, 그룹, 세션)은 아직 서비스 계층이
구현되지 않았다. 구현되면 이 문서와 `manifest.json` `service.public_methods`
를 함께 갱신한다.

## cache (`src/modules/cache/cache.py`, `Cache`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `get_render_result` | `source: str` | `Optional[RenderResult]` | — |
| `set_render_result` | `source: str`, `result: RenderResult` | `None` | — |
| `delete_render_cache` | `source: str` | `None` | — |
| `clear_all` | (없음) | `None` | — |

## parser (`src/modules/parser/parser.py`, `PlainTextBlockParser`)

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `parse` (staticmethod) | `source: str` | `ParserResult` | — |

## render (`src/modules/render/__init__.py` 가 재노출하는 순수 함수 모음)

`render` 모듈은 서비스 클래스가 아니라 상태 없는 순수 함수의 집합이다.
각 함수는 문자열(또는 리스트/딕셔너리로 표현된 파싱 결과)을 입력받아
이스케이프된 HTML 문자열을 반환하며, 예외를 던지지 않는다.

| 함수 | 입력 | 출력 |
|---|---|---|
| `escape_html` | `text: str` | `str` |
| `sanitize_url` | `url: str` | `Optional[str]` (안전하지 않으면 `None`) |
| `sanitize_css_value` | `value: str` | `Optional[str]` (안전하지 않으면 `None`) |
| `render_plain_paragraph` | `content: str` | `str` |
| `render_heading` | `level: int`, `content: str` | `str` |
| `generate_heading_id` | `text: str` | `str` |
| `render_internal_link` | `page: str`, `label: Optional[str] = None` | `str` |
| `render_external_link` | `url: str`, `label: Optional[str] = None` | `str` |
| `render_bold` | `text: str` | `str` |
| `render_italic` | `text: str` | `str` |
| `render_strike` | `text: str` | `str` |
| `render_unordered_list` | `items: List[Dict[str, Any]]` | `str` |
| `render_ordered_list` | `items: List[Dict[str, Any]]` | `str` |
| `render_line_break` | (없음) | `str` |
| `render_redirect_notice` | `target_page: str` | `str` |
| `render_categories_metadata` | `categories: List[str]` | `str` |
| `render_simple_table` | `table: Dict[str, Any]` | `str` |
| `render_footnotes_section` | `footnotes: List[str]` | `str` |
| `render_nowiki` | `content: str` | `str` |
| `render_code_block` | `content: str` | `str` |

## search (계약 이전 단계)

`manifest.json` 은 `service.path` 를 `src/modules/search/service.py`,
`service.public_methods` 를 `["index", "search"]` 로 선언하지만, 이
파일은 아직 존재하지 않는다. 현재는 저장소 포트에 해당하는
`SearchAdapter`(`src/modules/search/adapter.py`)가 같은 이름의 메서드를
추상 메서드로 정의하고 있다.

| 메서드 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `index` | `document: SearchDocument` | `None` | — |
| `search` | `query: SearchQuery` | `List[SearchResult]` | — |

`SearchDocument`/`SearchQuery` 생성 시점에 각각
`EmptySearchDocumentIdError`/`EmptySearchDocumentTitleError`/
`EmptySearchQueryTermError` 가 발생할 수 있으나, 이는 `index`/`search`
메서드 자체의 계약이 아니라 인자로 넘기는 도메인 모델 생성자의 계약이다.
`service.py` 가 실제로 추가되면 이 절을 서비스 클래스 기준으로 갱신한다.

## admin / audit / jobs (아직 구현 없음)

세 모듈 모두 현재 저장소에는 `manifest.json` 과 `README.md` 만 있고
Python 구현(`service.py` 등)이 없다. manifest 가 선언한 공개 메서드
이름만 아래에 옮겨 적으며, 입력/출력 타입은 구현 태스크가 실제
시그니처를 정할 때 이 문서를 갱신해 채운다.

| 모듈 | 선언된 공개 메서드 (manifest 기준) |
|---|---|
| admin | `block_user`, `unblock_user`, `protect_page`, `unprotect_page`, `submit_report`, `resolve_report` |
| audit | `record`, `list_events` |
| jobs | `enqueue`, `run_sync`, `get_status` |

## 관련 문서

- `docs/php-replacement-strategy.md` — "PHP 구현은 Python 구현과 같은
  공개 서비스 메서드 이름·입력·출력 의미를 가져야 한다"는 원칙.
- `docs/module-contract-manifest-schema.md` — `service.public_methods`
  가 속하는 manifest 스키마.
- `docs/dto-naming-convention.md` — 이 문서가 다루지 않는 API 계층
  Request/Response DTO 계약.
- `docs/portable-exception-code-policy.md` — 이 문서가 나열한 예외
  클래스가 실어 날라야 하는 안정적 error code 정책.
- `docs/portability-glossary.md` — Contract 용어 정의.
