# Shared Fixtures

이 디렉터리는 특정 모듈 하나에 속하지 않는 교차언어(cross-language)
fixture를 둔다. 위치 규칙은 `docs/fixture-directory-convention.md` 를
따른다.

- 모듈 하나의 서비스 동작만 검증하는 fixture는 여기가 아니라
  `tests/modules/<module>/fixtures/` 에 둔다.
- 이 디렉터리는 여러 모듈이 함께 참조하는 fixture(예: 교차언어 fixture
  JSON Schema, DB 이식 시드 데이터)를 위한 자리다. 실제 내용은 각 태스크
  (0369 Add cross-language fixture schema, 0490 Add DB portable seed
  fixtures 등)가 채운다.
- 파일 형식은 JSON을 기본으로 한다.

## 하위 디렉터리

- `schema/` — 교차언어 fixture 자체의 JSON Schema(0369). 개별 fixture
  파일(`input`/`expected`/`errors`)이 따라야 하는 구조를 정의한다. 자세한
  설명은 `docs/cross-language-fixture-schema.md` 참고.
