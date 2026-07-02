# Module Contract Manifest Schema

이 문서는 `docs/php-replacement-strategy.md` 가 요구하는 모듈 계약
manifest 의 스키마를 고정한다. Phase A: PHP Replacement Contract,
0351-0390 의 산출물이다.

manifest 는 `docs/portability-glossary.md` 가 정의한 **Contract** 의 일부이며,
모듈 하나(`src/modules/<module>`)의 언어 독립 계약 위치를 선언한다. 이 문서는
스키마 자체만 고정하며, 개별 모듈의 실제 manifest 내용(document, revision,
parser 등)은 이후 태스크(0354-0364)가 채운다.

## 스키마 정의 위치

기계 판독 가능한 JSON Schema(draft 2020-12)는
`src/modules/module_manifest.schema.json` 에 있다. 이후 검증 스크립트(0365,
0366)는 이 파일을 기준으로 각 모듈의 manifest 를 검사한다.

## manifest 파일 위치 규칙

각 모듈의 manifest 는 `src/modules/<module>/manifest.json` 에 둔다. 모듈
디렉터리 하나당 정확히 하나의 manifest 파일을 가지며, 여러 모듈이 하나의
manifest 를 공유하지 않는다.

## 필수 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `schema_version` | string | 이 문서가 따르는 스키마 버전. 현재 `"1.0"` 고정. |
| `module` | string | 모듈 이름. `src/modules/<module>` 디렉터리 이름과 일치. |
| `summary` | string | 모듈 책임 한 줄 요약. `docs/modules.md` 와 모순되지 않아야 함. |
| `port` | object | PHP 전환(port) 작업 자체의 상태와 대응 위치. |
| `service` | object | 도메인 서비스 계층 위치와 공개 메서드 목록. |
| `repository` | object | 저장소 포트(ABC 인터페이스)와 어댑터 위치. |
| `fixtures` | object | 언어 독립 parity fixture 디렉터리 위치. |

### `port`

- `source_path` (필수): Python 구현 루트 경로. 보통
  `src/modules/<module>`.
- `target_namespace` (선택): PHP 대응 네임스페이스 후보. 아직 정해지지
  않았으면 생략한다.
- `status` (필수): `not_started` / `in_progress` / `ready` 중 하나.
  `ready` 는 `docs/php-replacement-strategy.md` 의 readiness gate 5개
  조건을 모두 만족할 때만 쓴다.

### `service`

- `path` (필수): 서비스 구현 파일 경로. 보통
  `src/modules/<module>/service.py`.
- `public_methods` (필수, 최소 1개): PHP 구현이 이름·입력·출력 의미를
  그대로 재현해야 하는 공개 메서드 이름 목록. 여기 없는 메서드나 내부
  필드에 다른 모듈이나 adapter 가 직접 의존하는 것은 금지된 결합이다
  (`docs/php-replacement-strategy.md` 의 Forbidden Couplings 참고).

### `repository`

- `port_path` (필수): 저장소 포트 인터페이스(ABC) 파일 경로. 보통
  `src/modules/<module>/repository.py`.
- `interface` (필수): 저장소 포트 ABC 클래스 이름 (예: `DocumentRepository`).
- `adapter_path` (선택): 구체 구현 위치. `port_path` 와 같은 파일이면
  생략한다.

### `fixtures`

- `path` (필수): fixture 디렉터리 경로. 보통
  `tests/modules/<module>/fixtures`.
- `format` (필수): fixture 파일 형식. 언어 독립성을 위해 `"json"` 고정.

### `contract_notes` (선택)

모듈마다 다른 계약 세부사항(예: cache 모듈의 선택 가능한 backend, jobs
모듈의 shared hosting sync fallback 기본값, audit 모듈의 append-only 실패
정책)을 자유 서술로 기록하는 확장 지점이다. 새 필드를 스키마에 추가하지
않고도 모듈 고유 사항을 남길 수 있게 한다.

## 예시

```json
{
  "schema_version": "1.0",
  "module": "example",
  "summary": "이 항목은 실제 모듈이 아니라 필드 사용법을 보여주는 템플릿이다.",
  "port": {
    "source_path": "src/modules/example",
    "status": "not_started"
  },
  "service": {
    "path": "src/modules/example/service.py",
    "public_methods": ["do_something"]
  },
  "repository": {
    "port_path": "src/modules/example/repository.py",
    "interface": "ExampleRepository"
  },
  "fixtures": {
    "path": "tests/modules/example/fixtures",
    "format": "json"
  }
}
```

## 관련 문서

- `docs/php-replacement-strategy.md` — 이 manifest 가 충족해야 하는 readiness
  gate 와 금지된 결합.
- `docs/portability-glossary.md` — Port/Adapter/Contract/Fixture 용어 정의.
- `docs/modules.md` — 모듈 책임과 의존 규칙.
- `src/modules/module_manifest.schema.json` — 기계 판독 가능한 JSON Schema.
