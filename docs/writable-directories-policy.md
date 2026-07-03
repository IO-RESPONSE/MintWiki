# Writable Directories Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.
[Public Docroot Policy](public-docroot-policy.md)와
[Config File Permission Policy](config-file-permission-policy.md)을 기반으로,
공용 웹호스팅에서 애플리케이션이 쓸 수 있는 디렉터리의 위치와 권한 원칙을 정의한다.

## 목적

공용 웹호스팅에서는 PHP 프로세스가 쓸 수 있는 경로를 최소화해야 한다.
이 문서는 런타임 쓰기 경로를 `cache`, `uploads`, `logs`로 분리하여 다음을 보장한다:

- 캐시 삭제가 업로드 파일이나 로그를 지우지 않는다.
- 업로드 파일 정리 작업이 캐시와 로그에 영향을 주지 않는다.
- 로그 파일이 웹에서 직접 내려받아지거나 업로드 파일과 섞이지 않는다.
- installer requirement check가 검사할 writable directory 목록을 고정한다.

## 적용 범위

- 공용 웹호스팅(cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 런타임
- installer가 설치 전 검사해야 하는 런타임 쓰기 디렉터리
- 애플리케이션이 실행 중 생성하는 캐시, 업로드 파일, 로그

적용되지 않는 것:

- 데이터베이스 백업 보관 정책
- 업로드 허용 확장자, MIME 검사, 파일명 생성 규칙
- 로그 로테이션 구현
- PHP 코드 또는 installer 구현

## 1. 기준 디렉터리 구조

쓰기 가능한 런타임 파일은 document root 밖의 `storage/` 아래에 둔다.
`php/public/` 또는 호스팅의 공개 document root 안에는 쓰기 디렉터리를 만들지 않는다.

```
/home/user/wiki/
├── php/
│   ├── public/              # document root, 쓰기 금지
│   ├── src/
│   └── config/
└── storage/                 # 비공개 런타임 저장소
    ├── cache/               # 재생성 가능한 캐시
    ├── uploads/             # 사용자 업로드 원본/파생 파일
    └── logs/                # 애플리케이션 로그
```

## 2. 디렉터리별 책임

| 디렉터리 | 쓰기 주체 | 보존 기준 | 공개 접근 | 비고 |
|---|---|---|---|---|
| `storage/cache/` | PHP 런타임, installer | 삭제 가능 | 금지 | 렌더링 캐시, 임시 계산 결과처럼 재생성 가능한 파일만 저장한다. |
| `storage/uploads/` | PHP 런타임 | 보존 필요 | front controller를 통한 간접 접근만 허용 | 사용자 파일은 캐시 정리와 분리한다. |
| `storage/logs/` | PHP 런타임 | 보존 필요 | 금지 | 오류, 감사 보조 로그, 진단 로그를 저장한다. |

`storage/cache/`, `storage/uploads/`, `storage/logs/` 사이에 심볼릭 링크를 두지 않는다.
각 디렉터리는 독립적으로 생성, 권한 검사, 정리할 수 있어야 한다.

## 3. 권한 원칙

기본 권한은 shared hosting에서 PHP 프로세스가 호스팅 계정 사용자로 실행되는 경우를 기준으로 한다.

```bash
chmod 750 storage
chmod 750 storage/cache
chmod 750 storage/uploads
chmod 750 storage/logs
```

호스팅사가 그룹 기반 웹 서버 실행 모델을 쓰는 경우에는 소유자와 웹 서버 그룹만 접근하도록 설정한다.

```bash
chown -R user:www-data storage
chmod 750 storage storage/cache storage/uploads storage/logs
```

권한이 더 느슨한 `777`은 기본값으로 사용하지 않는다. 일부 shared hosting에서 임시 문제 해결용으로
요구하더라도 운영 상태로 남기지 않고, installer 또는 진단 화면은 이를 경고로 보고해야 한다.

## 4. Installer 검사 기준

installer requirement check는 다음 조건을 각각 독립적으로 확인한다:

- `storage/`가 document root 밖에 있다.
- `storage/cache/`, `storage/uploads/`, `storage/logs/` 세 디렉터리가 모두 존재한다.
- 세 디렉터리 각각에 대해 디렉터리 여부, 쓰기 가능 여부, 읽기 가능 여부를 검사한다.
- 세 디렉터리 중 하나의 실패를 다른 디렉터리 성공으로 대체하지 않는다.
- 검사 중 만든 임시 파일은 해당 디렉터리 안에서 바로 삭제한다.

검사 결과 메시지는 디렉터리 이름을 분리해서 표시한다. 예를 들어 `storage/cache/`만 실패하면
`uploads`와 `logs`까지 실패한 것처럼 묶어서 보고하지 않는다.

## 5. 보안 기준

- `storage/` 전체는 document root 밖에 두며, 웹 서버 직접 접근을 금지한다.
- 업로드 파일 다운로드가 필요하면 `public/index.php`를 거쳐 권한 검사 후 스트리밍한다.
- `storage/uploads/`에는 PHP 스크립트를 실행 가능한 상태로 두지 않는다.
- `storage/logs/`에는 요청 헤더, 쿠키, 세션 ID, DB 비밀번호 같은 민감값을 원문으로 남기지 않는다.
- `storage/cache/`는 언제든 삭제될 수 있으므로 사용자 원본 파일이나 감사 기록을 저장하지 않는다.

## 6. 운영 체크리스트

- [ ] 배포 패키지에 `storage/cache/`, `storage/uploads/`, `storage/logs/` 생성 절차가 있다.
- [ ] 세 디렉터리는 document root 밖에 있다.
- [ ] 세 디렉터리 권한은 owner/group 기반 최소 권한이며 `777`이 아니다.
- [ ] 캐시 정리 명령은 `storage/cache/`만 대상으로 한다.
- [ ] 업로드 백업 또는 복원 절차는 `storage/uploads/`를 별도 대상으로 다룬다.
- [ ] 로그 수집과 삭제 절차는 `storage/logs/`만 대상으로 한다.

## 이 문서가 하지 않는 것

- installer requirement check 코드를 작성하지 않는다.
- 업로드 파일 저장소, 로그 writer, 캐시 backend를 구현하지 않는다.
- 호스팅사별 제어판 화면 절차를 정의하지 않는다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — 호스팅 환경 요구사항.
- [Public Docroot Policy](public-docroot-policy.md) — document root와 비공개 디렉터리 분리.
- [Config File Permission Policy](config-file-permission-policy.md) — 민감 설정 파일 권한.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — upload/path traversal 보안 기준.
