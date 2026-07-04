# php/scripts

`php/` 트리 전용 QA 명령을 모아 두는 디렉터리. Phase B: PHP Runtime
Skeleton, 0391-0440 의 0430 산출물이다
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

- `test.sh` — `php/tests/` 아래 모든 `*Test.php`를 찾아 `php` CLI로
  하나씩 실행하고(`docs/php-test-bootstrap.md`가 정한 실행 방식과 동일),
  파일별 `PASS`/`FAIL`과 전체 통과 개수를 출력한다. 하나라도 실패하면
  실패한 파일의 stderr/stdout을 함께 출력하고 exit code 1로 끝난다.
  `vendor/autoload.php`가 없으면(=`composer install` 미실행) 바로 안내
  메시지와 함께 exit code 1로 끝난다. `php/`에서
  `scripts/test.sh`로, 저장소 루트에서 `php/scripts/test.sh`로 실행할 수
  있다(스크립트가 자기 위치 기준으로 `php/`로 이동한다).
- `qa.sh` — `test.sh`를 호출하는 단일 진입점. 정적 분석 도구(PHPStan/
  Psalm)는 아직 도입 전이므로(`docs/php-static-analysis-plan.md`) 지금은
  테스트 실행만 하지만, 그 문서의 도입 트리거 조건이 성립하면 정적
  분석 단계를 이 스크립트에 추가한다. "test/static check 명령을 한 곳에
  둔다"는 0430 Notes 요구사항을 충족하는 지점이다.
- `build-package.sh` — 공유 호스팅 배포 패키지 빌드의 골격 스크립트.
  `php/deployment-package-manifest.json`을 읽고 기본 `--without-vendor`
  모드와 `--with-vendor` 모드의 입력 목록을 분리해 출력한다. 실제
  아카이브 생성은 후속 패키징 태스크에서 추가한다.
- `cache-clear.sh` — 애플리케이션 캐시 비우기 명령의 골격 스크립트.
  현재 PHP 캐시 포트는 `get`/`set`/`delete` 기본 계약만 고정되어 있어
  전체 삭제 백엔드 연결은 아직 없다. 이 스크립트는 실행 가능한 CLI
  진입점과 help/오류 처리를 먼저 고정하고, 실제 캐시 삭제는 후속
  태스크에서 추가한다.
- `post-cutover-validate.sh` — Python에서 PHP로 최종 cutover 후 실행할
  검증 명령의 골격 스크립트. `--base-url`로 공개 URL을 받아 `/health`,
  DB 연결/schema 준비 상태, 문서 생성, 생성 문서 조회 순서의 검증 계획을
  출력한다. 실제 HTTP 요청, DB 진단, 문서 쓰기 자동화는 후속 태스크에서
  추가한다.

공유 호스팅에서 CLI 실행 권한이 없으면, 호스팅 파일 관리자나 SFTP로
설정된 캐시 디렉터리의 **내용만** 비우는 운영 절차를 사용한다. 캐시
디렉터리 자체는 삭제하지 않는다. 디렉터리 권한과 경로는 설치/운영
문서가 정한 값을 따른다.

저장소 루트의 `scripts/qa.sh`가 이 스크립트를 선택 실행하도록 연결하는
것은 이 태스크의 범위가 아니다 — 0431(Add root QA hook for optional PHP)
이 담당한다.
