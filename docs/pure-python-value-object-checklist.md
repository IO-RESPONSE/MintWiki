# Pure Python Value Object Checklist

이 문서는 `src/modules/<module>/model.py` 에 선언된 도메인 value object(문서,
리비전, 사용자 등 순수 Python 클래스)가 PHP 로 1:1 포팅 가능한 형태를
유지하도록, `dataclass`/기본값(default)/`typing` 사용을 제한하는
체크리스트를 고정한다. Phase A: PHP Replacement Contract, 0351-0390 의
산출물이다.

이 문서는 `AGENTS.md` 의 이식성 계층 규칙("도메인 계층은 표준 라이브러리와
프로젝트 내부 모듈만 사용해 순수 Python 으로 유지한다")을 value object 의
**클래스 정의 형태** 수준까지 구체화한다. `schema.py` 의 pydantic DTO 는
대상이 아니다 — 그쪽 이름 규칙은 `docs/dto-naming-convention.md` 가 이미
다룬다.

## 왜 제한하는가

- `dataclass` 는 `__init__`/`__eq__`/`__repr__` 를 데코레이터가 자동
  생성한다. PHP 에는 이런 데코레이터가 없으므로, 자동 생성된 필드 목록을
  보고 PHP 생성자를 손으로 옮겨 적어야 한다면 필드 순서·기본값·타입을
  누락하기 쉽다. 명시적 `__init__` 을 직접 쓰면 그 시그니처 자체가 이미
  PHP 생성자 시그니처의 원본이 된다.
- Python 의 함수 기본값은 함수 정의 시점에 한 번만 평가된다(가변 기본값
  함정). `list`/`dict` 리터럴을 기본값으로 직접 쓰면 인스턴스 간에
  값이 공유되는 버그로 이어지고, PHP 로 그대로 옮기면 완전히 다른(그리고
  더 나쁜) 동작이 된다. `None` 기본값 + 본문에서 정규화하는 패턴만
  허용하면 두 언어에서 동일하게 안전한 번역이 가능하다.
- `typing` 모듈은 `Generic`/`TypeVar`/`Protocol`/`TypedDict`/`NewType` 처럼
  PHP 타입 시스템에 대응물이 없는 기능을 제공한다. value object 가 이런
  기능에 의존하면 계약을 언어 독립적으로 표현할 수 없다.

## 체크리스트

`src/modules/<module>/model.py` 에 새 value object 클래스를 추가하거나
기존 클래스를 수정할 때 아래 항목을 모두 만족해야 한다.

### 1. dataclass 사용 제한

- [ ] `@dataclass` (또는 `@dataclasses.dataclass`) 데코레이터를 쓰지
      않는다. 생성자는 항상 명시적 `def __init__(self, ...):` 로 적는다.
      예: `Document`(`src/modules/document/model.py`),
      `Revision`(`src/modules/revision/model.py`),
      `User`(`src/modules/user/model.py`),
      `Heading`/`Footnote`/`RenderMetadata`/`RenderResult`
      (`src/modules/render/model.py`),
      `ParserDiagnostic`/`ParserResult`(`src/modules/parser/model.py`).
- [ ] `dataclasses.field(default_factory=...)` 를 쓰지 않는다(위 항목에서
      `dataclass` 자체를 금지하므로 자동으로 배제된다).

### 2. 기본값(default) 제한

- [ ] 생성자 매개변수의 기본값은 `None` 또는 불변 리터럴(`str`/`int`/
      `float`/`bool` 리터럴)만 쓴다. 예: `current_revision_id:
      Optional[str] = None`(`Document`), `code: Optional[str] = None`
      (`ParserDiagnostic`).
- [ ] `list`/`dict` 리터럴(`[]`, `{}`)을 기본값으로 직접 쓰지 않는다.
      대신 `Optional[List[X]] = None` 으로 선언하고, 생성자 본문에서
      `headings or []` 처럼 정규화한다. 예: `RenderMetadata.__init__`
      (`src/modules/render/model.py`)의 `headings`/`links`/`categories`/
      `footnotes` 매개변수 — 넷 다 `Optional[List[...]] = None` 으로
      선언되고 본문에서 `or []` 로 정규화된다.
- [ ] 함수 호출이나 표현식을 기본값으로 쓰지 않는다(예:
      `created_at: datetime = datetime.now()`). 이런 값은 호출자(서비스
      계층)가 명시적으로 넘겨야 한다 — 생성자 정의 시점에 한 번만
      평가되는 Python 함정을 애초에 만들지 않는다.

### 3. typing 사용 제한

- [ ] value object 의 타입 힌트는 `Optional`, `List`, `Dict`, `Any`,
      `Literal`(문자열 리터럴 집합) 다섯 가지로만 한정한다. 예:
      `Literal["error", "warning", "info"]`
      (`ParserDiagnostic.severity`, `src/modules/parser/model.py`).
- [ ] `Union`(`Optional` 이 아닌, 즉 `None` 을 포함하지 않거나 3개 이상
      타입을 묶는 `Union`), `Generic`, `TypeVar`, `Protocol`,
      `TypedDict`, `NewType`, `Callable` 을 쓰지 않는다. PHP 타입
      시스템에 직접 대응물이 없어, 계약을 언어 독립적으로 표현할 수
      없다.
- [ ] `Literal` 로 고정한 값 집합이 바뀌면, 그 값을 실제로 분기하는 서비스
      계층 코드와 관련 fixture 를 함께 갱신한다 — value object 의
      `Literal` 은 별도의 정답 소스가 아니다.

## PHP 대응 표

| Python 표현 | PHP 대응 |
|---|---|
| `Optional[str] = None` | `?string $x = null` |
| `Optional[List[X]] = None` + `x or []` | `?array $x = null` + `$this->x = $x ?? [];` |
| `Literal["a", "b", "c"]` | 허용 문자열 상수 집합을 docblock/enum 으로 명시 |
| `Dict[str, Any]` | 연관 배열(`array`) |
| 명시적 `__init__` | 명시적 `__construct` |

## 적용 대상

- 이 체크리스트는 `src/modules/<module>/model.py` 에 선언된 도메인
  value object 에만 적용된다.
- `schema.py` 의 pydantic DTO(Request/Response) 는 대상이 아니다 —
  프레임워크 계층 코드이며 이름 규칙은
  `docs/dto-naming-convention.md` 가 다룬다.
- `service.py` 에 선언되는 `ReadModel`(`docs/dto-naming-convention.md`
  참고)도 순수 Python 클래스라면 이 체크리스트를 동일하게 적용한다.

## 관련 문서

- `AGENTS.md` — 이식성 계층 규칙과 도메인 계층 프레임워크 금지 목록.
- `docs/php-replacement-strategy.md` — 모듈 단위 1:1 교체 원칙.
- `docs/dto-naming-convention.md` — `schema.py`/`ReadModel` DTO 이름
  규칙(이 문서가 다루지 않는 영역).
- `docs/php-namespace-mapping.md` — Python 클래스 이름을 PHP 클래스
  이름으로 옮기는 규칙.
- `docs/portability-glossary.md` — Contract 용어 정의.
