# Shared Hosting Security Checklist

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅 배포 전후에 확인해야 하는 최소 보안 체크리스트를 정의한다.
이 문서는 배포자가 이미 작성된 정책 문서를 빠르게 검증할 수 있도록 public path,
config, installer, permissions 항목을 하나의 운영 점검표로 묶는다.

## 목적과 범위

- **대상**: 공용 웹호스팅 배포 담당자, installer QA 담당자, 운영 점검 담당자.
- **다루는 것**:
  - 공개 document root와 비공개 경로 분리 확인.
  - 설정 파일과 민감값 보관 위치 확인.
  - installer 노출, lock file, 완료 후 차단 기준 확인.
  - 파일 및 디렉터리 권한 기준 확인.
- **다루지 않는 것**:
  - 호스팅사별 제어판 화면 절차.
  - 코드 수준 보안 기능 구현.
  - TLS 인증서 발급, WAF, CDN 같은 외부 인프라 설정.

## 1. Public Path 체크리스트

웹 서버 document root는 `php/public/` 하나만 가리켜야 한다.

- [ ] `DocumentRoot` 또는 호스팅 패널의 public path가 `php/public/`으로 설정되어 있다.
- [ ] `php/src/`, `php/config/`, `php/vendor/`, `db/`, `docs/`, `tests/`, `storage/`는 document root 밖에 있다.
- [ ] `https://example.com/config/`, `https://example.com/vendor/`, `https://example.com/storage/` 요청은 403 또는 404를 반환한다.
- [ ] 정적 파일은 `php/public/assets/` 아래 파일만 직접 서빙한다.
- [ ] 사용자 업로드 파일은 직접 URL로 노출하지 않고 front controller를 거쳐 권한 검사 후 스트리밍한다.

## 2. Config 체크리스트

설정 파일은 웹에서 직접 접근할 수 없는 위치에 두고, 민감값은 샘플 파일에 남기지 않는다.

- [ ] 실제 DB 자격증명은 `php/config/*.sample`이 아니라 비공개 `php/config/` 또는 호스팅 로컬 설정 파일에만 있다.
- [ ] `database.php`, `local-config.php`, `.env` 계열 파일은 document root 밖에 있다.
- [ ] 설정 파일 권한은 기본적으로 `chmod 640`, 단일 사용자 실행 환경에서는 `chmod 600`을 사용한다.
- [ ] 설정 디렉터리는 `chmod 750`이며, `777` 권한으로 운영하지 않는다.
- [ ] 오류 화면, installer 진단, 로그에 DB 비밀번호, DSN 전체 문자열, API 키를 원문으로 표시하지 않는다.

## 3. Installer 체크리스트

installer는 설치 전 검사를 제공하되, 설치 완료 후에는 재실행되지 않아야 한다.

- [ ] installer requirement check가 PHP 버전, PDO MariaDB 드라이버, URL rewrite, 쓰기 디렉터리, 설정 파일 생성 가능 여부를 검사한다.
- [ ] installer는 `storage/cache/`, `storage/uploads/`, `storage/logs/`를 각각 독립적으로 검사한다.
- [ ] 설치 완료 후 `storage/installer/install.lock` 같은 lock file이 document root 밖에 생성된다.
- [ ] lock file이 있으면 `/installer` 계열 route는 HTTP 403과 `installation_already_complete` 오류 코드로 차단된다.
- [ ] installer 실패 메시지는 필요한 조치만 보여 주고, 비밀번호나 secret 값을 출력하지 않는다.
- [ ] 운영 중 재설치는 백업 확인과 수동 lock file 삭제 절차 없이는 허용하지 않는다.

## 4. Permissions 체크리스트

권한은 shared hosting에서 PHP가 읽거나 써야 하는 경로만 허용하는 최소 권한으로 둔다.

- [ ] `php/public/`, `php/src/`, `php/vendor/`, `db/`는 PHP 런타임이 쓸 수 없는 읽기 전용 배포 파일로 취급한다.
- [ ] `storage/`와 하위 쓰기 디렉터리는 document root 밖에 있다.
- [ ] `storage/cache/`, `storage/uploads/`, `storage/logs/` 권한은 기본적으로 `chmod 750`이다.
- [ ] 업로드 디렉터리에는 PHP 스크립트를 실행 가능한 상태로 두지 않는다.
- [ ] 로그 파일은 웹에서 직접 내려받을 수 없고, 세션 ID, 쿠키, 비밀번호를 원문으로 보관하지 않는다.
- [ ] 임시 문제 해결을 위해 `777`을 사용한 경우 운영 전 `750` 또는 더 엄격한 권한으로 되돌린다.

## 5. 배포 전 최종 확인

- [ ] 새 배포 패키지를 올린 뒤 `php/public/` 외부 경로가 URL로 열리지 않는지 확인했다.
- [ ] 설정 파일 샘플과 실제 설정 파일을 구분했고, 실제 설정 파일은 백업 범위에 포함했다.
- [ ] installer 완료 후 lock file과 installer route 차단을 확인했다.
- [ ] 쓰기 디렉터리 세 곳의 권한과 임시 파일 생성/삭제를 확인했다.
- [ ] 오류 화면과 로그에 민감값이 노출되지 않는지 대표 실패 케이스로 확인했다.

## 관련 문서

- [Public Docroot Policy](public-docroot-policy.md) — document root와 비공개 디렉터리 분리.
- [Config File Permission Policy](config-file-permission-policy.md) — 설정 파일 위치와 권한 기준.
- [Installer Lock File Policy](installer-lock-file-policy.md) — 설치 완료 후 installer 차단 기준.
- [Writable Directories Policy](writable-directories-policy.md) — 쓰기 디렉터리 위치와 권한 기준.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — PHP 런타임 보안 기준.
