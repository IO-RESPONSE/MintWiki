# php/src/App

애플리케이션 부트스트랩 계층 (`MintWiki\App` namespace). 태스크 0415에서
`ConfigLoader.php`와 함께 처음 추가되었다.

`docs/php-namespace-mapping.md`가 명시하듯 이 디렉터리는 모듈이 아니므로
그 문서의 `MintWiki\<Module>` 매핑 대상이 아니다 — Python 쪽 대응 위치는
`src/app`(FastAPI 부트스트랩: 엔트리포인트·설정·DB 엔진 초기화)이다.

- `ConfigLoader.php` (태스크 0415) — Python `src/app/config.py`의
  `Settings`와 대응하는 설정 읽기 계약. `WIKI_` 접두어 환경변수를
  최우선으로 하고, 없으면 생성자로 전달된 file-value 배열을, 그것도
  없으면 호출자가 넘긴 `$default`를 반환한다.
- `LocalConfigLoader.php` (태스크 0616) — 로컬 설정 파일들(`.env`와
  `local-config.php`)을 읽어서 ConfigLoader에 전달할 값 배열을
  구성한다. 환경변수가 없어도 파일 설정으로부터 값을 읽을 수 있다.
  `.env` 파일이 `local-config.php`보다 우선한다.
- `ErrorCodeRegistry.php` (태스크 0416) — `docs/portable-exception-code-
  policy.md`가 정한 `<module>.<reason>` error code 형식 검증과 등록된
  code 조회를 한 곳에서 제공한다. code 값의 정본은 여전히 각 모듈 예외
  클래스의 `CODE` 상수이며, 이 registry는 그 값을 참조만 한다 — 현재는
  `MintWiki\Document`의 세 code(`document.empty_title`,
  `document.duplicate_title`, `document.not_found`)가 등록되어 있고,
  Python `tests/modules/document/test_error_codes.py`와 이름이 같다.
