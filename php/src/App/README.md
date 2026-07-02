# php/src/App

애플리케이션 부트스트랩 계층 (`MintWiki\App` namespace). 태스크 0415에서
`ConfigLoader.php`와 함께 처음 추가되었다.

`docs/php-namespace-mapping.md`가 명시하듯 이 디렉터리는 모듈이 아니므로
그 문서의 `MintWiki\<Module>` 매핑 대상이 아니다 — Python 쪽 대응 위치는
`src/app`(FastAPI 부트스트랩: 엔트리포인트·설정·DB 엔진 초기화)이다.

- `ConfigLoader.php` (태스크 0415) — Python `src/app/config.py`의
  `Settings`와 대응하는 설정 읽기 계약. `WIKI_` 접두어 환경변수를
  최우선으로 하고, 없으면 생성자로 전달된 file-value 배열(파일 파싱은
  아직 이 태스크 범위 밖)을, 그것도 없으면 호출자가 넘긴 `$default`를
  반환한다. `.env`/config 파일 자체를 읽는 실제 파서는 0616 "local
  config loader"에서 추가된다.
