# Export Directory Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.
[Public Docroot Policy](public-docroot-policy.md)와
[Writable Directories Policy](writable-directories-policy.md)를 기반으로,
공용 웹호스팅에서 export 파일을 생성하고 보관할 디렉터리 정책을 정의한다.

## 목적

문서, 사용자, 설정 진단 결과처럼 운영자가 내려받을 수 있는 export 파일은
민감한 데이터와 내부 식별자를 포함할 수 있다. 이 문서는 다음을 보장한다:

- export 파일은 기본적으로 public document root 밖에 저장한다.
- export 저장소는 업로드, 캐시, 로그와 분리한다.
- 웹 브라우저 직접 접근 대신 인증된 front controller 다운로드를 사용한다.
- installer requirement check가 확인할 export 디렉터리 조건을 고정한다.

## 적용 범위

- 공용 웹호스팅(cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 런타임
- installer 또는 관리자 기능이 생성하는 export 파일
- 운영자가 다운로드하기 전까지 임시 보관되는 export 결과물

적용되지 않는 것:

- 장기 백업 보관 정책
- export 파일 포맷, 스키마, 암호화 방식
- 외부 오브젝트 스토리지 연동
- PHP 코드 또는 installer 구현

## 1. 기준 디렉터리 구조

export 파일은 document root 밖의 `storage/exports/` 아래에 둔다.
`php/public/`, `public/`, `public_html/` 바로 아래에는 export 파일을 저장하지 않는다.

```
/home/user/wiki/
├── php/
│   ├── public/              # document root, export 저장 금지
│   └── src/
└── storage/                 # 비공개 런타임 저장소
    ├── cache/
    ├── uploads/
    ├── logs/
    └── exports/             # 관리자 export 결과물
```

`storage/exports/`는 `storage/uploads/`, `storage/cache/`, `storage/logs/`와
독립된 디렉터리여야 한다. 심볼릭 링크로 public document root나 업로드
디렉터리에 연결하지 않는다.

## 2. 저장 정책

| 항목 | 기준 |
|---|---|
| 기본 위치 | `storage/exports/` |
| 공개 접근 | 금지 |
| 다운로드 방식 | 인증된 관리자 요청이 `public/index.php`를 거쳐 스트리밍 |
| 보존 기간 | 짧은 임시 보관. 운영자가 받은 뒤 삭제 가능해야 함 |
| 파일명 | 예측하기 어려운 작업 ID 또는 토큰을 포함하되, 접근 제어를 대체하지 않음 |

export 파일은 사용자에게 직접 URL을 노출하는 정적 파일로 취급하지 않는다.
다운로드가 필요하면 front controller가 관리자 권한, export 소유자 또는 작업 ID,
만료 여부를 확인한 뒤 파일을 스트리밍한다.

## 3. 권한 원칙

기본 권한은 PHP 프로세스가 호스팅 계정 사용자로 실행되는 shared hosting을 기준으로 한다.

```bash
chmod 750 storage/exports
```

호스팅사가 그룹 기반 웹 서버 실행 모델을 쓰는 경우에는 소유자와 웹 서버 그룹만
접근하도록 설정한다.

```bash
chown user:www-data storage/exports
chmod 750 storage/exports
```

권한이 더 느슨한 `777`은 기본값으로 사용하지 않는다. installer 또는 진단 화면은
`storage/exports/`가 public document root 안에 있거나 `777`이면 운영 위험으로 보고한다.

## 4. Installer 검사 기준

installer requirement check는 다음 조건을 각각 확인한다:

- `storage/exports/`가 존재한다.
- `storage/exports/`가 디렉터리이며 document root 밖에 있다.
- PHP 런타임이 `storage/exports/`에 쓰기, 읽기, 삭제를 수행할 수 있다.
- 검사 중 만든 임시 export 파일은 검사 직후 삭제한다.
- `storage/exports/`가 `public/`, `php/public/`, `public_html/` 아래로 이어지는
  심볼릭 링크가 아니다.

검사 결과 메시지는 export 디렉터리 실패를 cache, uploads, logs 실패와 구분해서 표시한다.

## 5. 보안 기준

- export 파일에는 DB 자격증명, 세션 ID, 쿠키 값, 비밀번호 해시를 포함하지 않는다.
- export 파일은 public document root 밖에 저장하며 웹 서버 직접 접근을 금지한다.
- 다운로드 응답은 관리자 인증과 권한 검사를 통과한 요청에만 제공한다.
- 완료되었거나 만료된 export 파일은 정리 작업 대상이 되어야 한다.
- export 파일 정리는 `storage/exports/`만 대상으로 하며 uploads, cache, logs를 삭제하지 않는다.

## 6. 운영 체크리스트

- [ ] 배포 패키지에 `storage/exports/` 생성 절차가 있다.
- [ ] `storage/exports/`는 document root 밖에 있다.
- [ ] `storage/exports/` 권한은 owner/group 기반 최소 권한이며 `777`이 아니다.
- [ ] export 다운로드는 `public/index.php`를 거쳐 권한 검사 후 스트리밍한다.
- [ ] export 정리 절차는 `storage/exports/`만 대상으로 한다.

## 이 문서가 하지 않는 것

- export 생성기나 다운로드 라우트를 구현하지 않는다.
- export 포맷과 호환성 버전을 정의하지 않는다.
- 장기 백업, 복원, 외부 저장소 정책을 정의하지 않는다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — 호스팅 환경 요구사항.
- [Public Docroot Policy](public-docroot-policy.md) — document root와 비공개 디렉터리 분리.
- [Writable Directories Policy](writable-directories-policy.md) — 런타임 쓰기 디렉터리 원칙.
- [Config File Permission Policy](config-file-permission-policy.md) — 민감 설정 파일 권한.
