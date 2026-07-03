# 0671 Port iowiki shared hosting

## Goal

iowiki.iwinv.net FTP-only shared hosting 포팅을 수행한다.

## Phase

Phase F: Live Shared Hosting Porting, 0671+.

## Scope

- deployment
- diagnostics
- docs

## Acceptance Criteria

- FTP-only 환경에서 docroot를 확인한다.
- 임시 `phpinfo()` 진단 파일로 PHP 버전, 필수 확장, loaded config, document root, rewrite 관련 환경을 확인한다.
- 진단 파일은 확인 후 삭제한다.
- 배포 패키지를 생성하고 FTP로 업로드한다.
- MariaDB 연결 설정을 서버 비공개 위치 또는 노출 방지 설정으로 배치한다.
- 설치 또는 schema 적용 흐름을 실행한다.
- `iowiki.iwinv.net`에서 HTTP 접속 smoke test를 수행한다.
- 설치 완료 후 installer lock, 파일 권한, 민감 파일 웹 노출 여부를 점검한다.
- 실제 FTP/DB 비밀번호는 저장소에 기록하지 않는다.

## Out of Scope

- 호스팅 계정 비밀번호를 저장소에 커밋하는 작업.
- unrelated feature work.
- 대규모 리팩터링.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`
- live HTTP smoke test against `https://iowiki.iwinv.net/` or the provider URL available at deployment time.

## Notes

FTP 접속 정보와 DB 비밀번호는 실행 시점에 임시 credential 파일 또는 환경변수로만 제공한다.
`phpinfo()`는 민감 정보가 포함될 수 있으므로 공개 URL에 오래 남기지 않는다.
