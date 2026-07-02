# DTO Naming Convention

이 문서는 `docs/php-replacement-strategy.md` 가 정의한 모듈 단위 1:1 교체
계약의 일부로, Python 쪽 데이터 전달 객체(`schema.py`의 pydantic 모델,
`service.py` 등에 정의된 읽기 전용 구조체)와 그에 대응하는 PHP DTO 가
따라야 할 이름 규칙을 고정한다. Phase A: PHP Replacement Contract,
0351-0390 의 산출물이다.

이 문서는 DTO 의 **이름과 역할 구분**만 다룬다. 서비스 메서드의 입출력
계약(어떤 메서드가 어떤 DTO 를 받고 돌려주는가)은 0377(Add service method
contract docs), 저장소 포트 계약은 0378(Add repository port contract
docs)이 각각 정의한다.

## 왜 이름을 고정하는가

- DTO 는 "외부에서 들어오는 입력인지", "외부로 나가는 출력인지", "모듈
  내부에서만 도는 조회 전용 구조체인지"에 따라 변경 시 영향 범위가
  전혀 다르다. 이름만 보고 그 범위를 구분할 수 있어야 리뷰와 PHP 포팅
  둘 다 안전해진다.
- `docs/php-namespace-mapping.md` 는 Python 클래스 이름을 PHP 클래스
  이름으로 그대로 옮기는 것을 원칙으로 삼는다. Python 쪽 이름이 역할을
  드러내지 않으면 PHP 쪽 이름도 같은 문제를 그대로 물려받는다.
- 같은 클래스를 입력과 출력 양쪽에 겸용하면, 한쪽 필드를 바꿀 때 다른
  쪽 계약을 실수로 함께 바꾸기 쉽다. 이름으로 역할을 고정하면 이런
  겸용을 리뷰에서 바로 알아볼 수 있다.

## 세 가지 DTO 역할

DTO 는 아래 세 역할 중 정확히 하나에 속하며, 클래스 이름의 suffix 로
역할을 드러낸다. 세 역할 외의 suffix(`Dto`, `Vo`, `Payload`, `Model`
단독 등)는 쓰지 않는다.

### Request

**Request** 는 모듈 외부(HTTP 핸들러, API 라우터)에서 서비스 메서드로
들어오는 입력 DTO 다.

- 이름은 `<Verb><Noun>Request` 형식이다 — 어떤 동작을 요청하는지 동사로
  드러낸다. 예: `CreateDocumentRequest`(`src/modules/document/schema.py`),
  `CreateThreadRequest`, `AddCommentRequest`
  (`src/modules/discussion/schema.py`).
- 서비스 메서드가 검증하기 전의 원본 외부 입력을 감싼다. 서비스 내부
  전용 필드(생성 시각, 내부 상태 등)를 담지 않는다.

### Response

**Response** 는 서비스 메서드나 API 핸들러가 모듈 외부로 돌려주는 출력
DTO 다.

- 이름은 `<Noun>Response` 형식이다 — 무엇에 대한 응답인지 명사로만
  드러내고 동사를 붙이지 않는다. 예: `DocumentResponse`
  (`src/modules/document/schema.py`), `ThreadResponse`, `CommentResponse`
  (`src/modules/discussion/schema.py`), `RevisionResponse`
  (`src/modules/revision/schema.py`).
- 목록을 돌려주는 응답은 `List<Noun>Response` 형식으로 감싼다. 예:
  `ListThreadsResponse`, `ListCommentsResponse`
  (`src/modules/discussion/schema.py`). 목록 자체를 배열로 그대로
  반환하지 않고, 단일 항목 `Response`(`ThreadResponse`,
  `CommentResponse`)를 감싼 wrapper 클래스로 둔다.
- 클라이언트에 노출해도 되는 필드만 담는다. 내부 구현 세부사항(원본
  DB row, 캐시 메타데이터 등)을 그대로 흘려보내지 않는다.

### ReadModel

**ReadModel** 은 모듈 내부(서비스 계층 간, 또는 같은 모듈의 여러
서비스 메서드 간)에서만 쓰는 조회 전용 DTO 다. 외부 API 계약이
아니다.

- 이름은 `<Noun>ReadModel` 형식이다. 예: `CurrentRevisionReadModel`
  (`src/modules/document/service.py`) — 문서의 메타데이터와 현재
  리비전 정보를 함께 실어 나르는 내부 조회 구조체.
- API 응답 형태와 필드가 반드시 일치할 필요는 없다. 여러 하위 조회
  결과를 서비스 내부에서 조합하기 위한 편의 구조체이며, 외부 계약이
  바뀌지 않아도 자유롭게 필드를 늘리거나 줄일 수 있다.
- 다른 모듈이나 adapter 가 직접 참조하지 않는다. 참조가 필요하면
  이는 이미 모듈 경계를 넘는 결합이므로, 그 모듈의 `Response` DTO 로
  변환해서 노출한다(`docs/php-replacement-strategy.md` 의 금지할 결합
  — "계약에 선언되지 않은 내부 필드에 다른 모듈이 직접 의존하는 것"
  참고).

## 어디에 선언하는가

- Request 와 Response 는 모듈의 `schema.py` 에 선언한다 — 모듈 계약의
  일부로서 API 경계에 노출되는 DTO 이기 때문이다.
- ReadModel 은 그것을 만들어 쓰는 구현 파일(`service.py` 등)에
  선언한다. `schema.py` 에 두지 않는다 — `schema.py` 는 외부 계약만
  담는 자리이며, ReadModel 은 계약이 아니다.

## PHP 대응 규칙

- PHP DTO 클래스 이름은 Python 클래스 이름을 그대로 유지한다
  (`docs/php-namespace-mapping.md` 의 "파일이 아니라 그 파일이 정의하는
  공개 클래스 이름을 기준으로 이름을 붙인다" 규칙을 따름). 예:
  Python `CreateDocumentRequest` → PHP `MintWiki\Document\CreateDocumentRequest`,
  Python `DocumentResponse` → PHP `MintWiki\Document\DocumentResponse`,
  Python `CurrentRevisionReadModel` → PHP
  `MintWiki\Document\CurrentRevisionReadModel`.
- `Request`/`Response`/`ReadModel` suffix 는 포팅 시에도 번역하거나
  줄이지 않고 그대로 유지한다. 두 언어의 DTO 이름이 문자 그대로
  같아야 parity 리뷰에서 어떤 Python DTO 가 어떤 PHP DTO 에 대응하는지
  바로 알 수 있다.
- Request/Response 는 Python `schema.py` 와 같은 층위, 즉
  `MintWiki\<Module>` namespace 바로 아래에 둔다. ReadModel 은 그것을
  만드는 구현 클래스(예: `MintWiki\Document\Service`)와 같은 파일 또는
  같은 namespace 계층에 둔다 — Python 쪽 선언 위치 규칙과 대칭을
  이룬다.

## 금지 사항

- `Request`/`Response`/`ReadModel` 세 suffix 외의 새 DTO suffix 를
  만들지 않는다.
- 하나의 클래스가 두 역할을 겸하지 않는다. 예를 들어 서비스 메서드의
  입력으로 쓰는 클래스를 그대로 API 응답으로 재사용하지 않는다 — 입력과
  출력 필드 집합이 우연히 같더라도 `Request` 와 `Response` 를 별도
  클래스로 선언한다.
- `ReadModel` 을 `schema.py` 에 두거나 API 응답으로 직접 노출하지
  않는다. 외부에 보여줘야 하는 필드가 생기면 `ReadModel` 자체를
  노출하지 말고, 그 필드를 담는 `Response` DTO 를 새로 선언한다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 모듈 단위 1:1 교체 원칙과
  금지할 결합.
- `docs/portability-glossary.md` — Contract 용어 정의.
- `docs/php-namespace-mapping.md` — Python 클래스 이름을 PHP
  namespace/클래스 이름으로 옮기는 규칙.
- `docs/module-contract-manifest-schema.md` — DTO 가 속하는 모듈 계약의
  범위.
