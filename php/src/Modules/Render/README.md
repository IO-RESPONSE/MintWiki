# php/src/Modules/Render

`MintWiki\Render` namespace 구현. 문서 source를 HTML로 렌더링하는
adapter와 도메인 모델을 포함한다.

## 클래스

### RenderResult (태스크 0581)

렌더링 결과를 나타내는 도메인 모델. 렌더링된 HTML과 메타데이터
(제목, 링크, 카테고리, 각주)를 포함한다.

### DocumentRenderer (태스크 0581)

source -> HTML 연결 지점을 정의하는 인터페이스.

### PlainTextDocumentRenderer (태스크 0581)

DocumentRenderer의 기본 구현으로, source를 평문으로 간주하고 기본
HTML escaping과 단락 분할만 수행한다. 파서와 렌더 함수들이 추가되면
이를 활용하도록 개선된다.

## 계약

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.render` → PHP `MintWiki\Render`). 대응하는 계약
manifest 는 `src/modules/render/manifest.json` 이다.
