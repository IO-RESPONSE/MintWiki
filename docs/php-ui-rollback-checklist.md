# PHP UI Rollback Checklist

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 롤백 절차 문서.
[PHP UI Architecture](php-ui-architecture.md), [PHP Static Asset Serving](php-static-asset-serving.md),
[PHP UI Cache Header Policy](php-ui-cache-header-policy.md), [PHP UI Static Asset Integrity Policy](php-ui-static-asset-integrity.md)
에서 정의한 UI 구조를 **shared hosting 환경에서 배포 후 오류 발생 시 안전하게 롤백**할 때 확인해야 할 체크리스트다.

UI 롤백은 단순한 파일 복원 이상의 고려가 필요하다. 특히 schema/UI 호환성이 중요하다:
- **새 UI가 구 schema를 지원하지 않는 경우**, UI 롤백만으로는 불충분하고 schema 롤백도 필요할 수 있다.
- **구 UI가 새 schema를 지원하지 않는 경우**, UI 롤백 후에도 데이터 호환성 문제가 발생할 수 있다.
- **asset 캐시 무효화를 하지 않으면**, 브라우저가 여전히 이전 버전의 CSS/JavaScript를 사용할 수 있다.

이 문서는 운영자 또는 배포 담당자가 **UI 오류 감지 직후** 와 **롤백 완료 후** 에 사용한다.

`docs/php-deployment-checklist.md` (Phase D 배포), `docs/php-runtime-phase-qa-checklist.md` (Phase B)
와 동일한 형식을 따른다 — 각 항목은 "무엇을 확인하는가"와 "어떤 자동화가
이미 이를 커버하는가"를 함께 적는다.

## 사용법

### 오류 감지 시 즉시 (배포 후 첫 10~30분)

```bash
# 1. 로컬 재현 (있으면)
scripts/test.sh
scripts/qa.sh
php -S 127.0.0.1:8000 -t php/public &
# 브라우저에서 오류 재현 시도

# 2. 원인 파악
# - git log 또는 git diff로 배포된 변경 내용 확인
# - browser DevTools에서 asset 로드 상태 확인
# - shared hosting의 error log 확인

# 3. schema/UI 호환성 확인
# - "배포된 UI가 현재 DB schema를 지원하나?"
# - "구 UI가 현재 DB schema를 지원하나?"
```

### 롤백 결정 후

```bash
# 1. 롤백 계획 수립 (이 문서의 절 1~3)
# - 롤백 범위 (UI만 vs. UI + schema)
# - asset 캐시 무효화 전략
# - 예상 복구 시간

# 2. 롤백 실행 (절 4)
# - shared hosting에 구 파일 복원
# - asset 버전 또는 캐시 무효화
# - 라우터/설정 재설정

# 3. 롤백 후 검증 (절 5)
# - 첫 페이지 렌더링 확인
# - 주요 기능 작동 확인
# - 오류 로그 확인

# 4. 지속적 모니터링 (절 6)
# - error log 감시
# - 사용자 피드백
# - health check 실행
```

## 1. 롤백 전 상태 파악 (Pre-Rollback Assessment)

오류를 감지했을 때, 롤백이 필요한지, 롤백 범위가 무엇인지 결정하기 위해
현재 상태를 파악한다.

### 1.1 오류 신호와 영향도 평가

- [ ] shared hosting의 error log에서 PHP 오류 또는 500 에러가 있는지 확인한다.
      shared hosting 제어판에서 error log 경로 확인(보통 `php_error.log`, `apache_error.log`).
      ```bash
      tail -100 /path/to/php_error.log | grep -E "Fatal error|Parse error|Warning"
      ```
      
- [ ] 브라우저의 DevTools Network tab에서 실패한 요청을 확인한다.
      - asset (CSS, JS)이 404/403으로 로드되는가?
      - HTML 응답이 500 에러를 반환하는가?
      - 특정 경로에서만 오류가 발생하는가, 전체 사이트인가?

- [ ] 로그인/폼 제출/문서 편집 같은 주요 기능이 작동하는지 빠르게 테스트한다.
      - 첫 페이지는 로드되는가?
      - 오류는 모든 페이지인가, 특정 기능만인가?

- [ ] 배포 이후 얼마나 많은 사용자가 영향받았는지 추정한다 (error log 빈도).
      오류 빈도가 높으면 빠른 롤백이 필요하다.

### 1.2 배포된 변경사항 확인

- [ ] git log를 통해 배포된 커밋을 확인한다.
      ```bash
      git log --oneline HEAD~5..HEAD
      # 또는 배포 branch 에서 develop/main 과 비교
      git diff main..HEAD --stat | head -20
      ```

- [ ] 배포된 변경이 무엇인지 파악한다:
      - UI 템플릿 변경인가?
      - asset (CSS, JS) 변경인가?
      - 라우터/핸들러 변경인가?
      - schema 변경과 함께인가?

- [ ] 직전 배포 (이전 버전)와 현재 배포의 차이를 비교한다.
      ```bash
      git show <previous-commit-hash>:php/public/index.php > /tmp/prev.php
      # 현재 버전과 비교
      diff /tmp/prev.php php/public/index.php
      ```

### 1.3 Schema/UI 호환성 확인

이 단계가 **가장 중요**하다. 오류의 근본 원인이 schema/UI 호환성일 수 있다.

- [ ] **배포된 UI가 현재 DB schema를 지원하나?**
      - 새 UI는 새 컬럼/테이블을 기대하나?
      - 새 UI는 구 schema에서 필드가 없으면 에러가 나는가?
      - 예: 새 버전이 `documents.created_at` 컬럼을 추가했는데, DB 마이그레이션이 실패했다면, 
        새 UI가 그 컬럼을 접근할 때 500 에러가 난다.
      
      검증 방법:
      ```bash
      # DB 스키마 최근 변경사항 확인
      git log -p --follow -- db/migrations/ | head -100
      
      # 또는 직접 DB 연결 후 컬럼 확인
      mysql -u user -p dbname -e "DESCRIBE documents;"
      ```

- [ ] **구 UI가 현재 DB schema를 지원하나?**
      - 롤백 후 구 UI가 새 schema의 데이터를 올바르게 렌더링하나?
      - 예: 새 schema에 `document.visibility` 컬럼이 추가되었고 기본값이 PUBLIC 이었다면, 
        구 UI가 이 필드를 무시해도 문제없다. 하지만 마이그레이션이 부분 적용되어 일부 행만 
        컬럼이 있다면, 구 UI가 `NULL` 을 처리할 때 오류가 날 수 있다.

- [ ] **asset versioning 호환성을 확인한다.**
      - 새 UI 템플릿이 새 asset URL(`?v=newhash`)을 기대하나?
      - 롤백 후 구 asset URL(`?v=oldhash`)을 사용하면, 브라우저 캐시에서 자동으로 
        새 파일을 받으므로 대부분의 경우 문제없다. 하지만 명시적인 asset 목록이 
        하드코딩되어 있다면 불일치가 발생할 수 있다.

**자동화**: 이 단계는 수동 분석이 필수다. CI/CD 파이프라인이 배포 전에
schema/UI 호환성을 미리 검증하는 것이 이상적 (Phase E 배포 자동화).

## 2. 롤백 범위 결정 (Rollback Scope Decision)

오류의 원인에 따라 롤백 범위를 결정한다.

### 2.1 UI만 롤백

**상황**: 새 UI 템플릿/asset에 오류가 있지만, DB schema는 호환성이 있다.
- 예: CSS에 구문 오류가 있어 페이지가 깨졌다.
- 예: 새 라우터가 404를 반환한다.
- 예: HTML 이스케이핑 오류로 JavaScript 실행 오류가 난다.

**롤백 범위**:
- `php/public/` (HTML 템플릿, asset CSS/JS)
- `php/src/Ui/` (UI 라우터/핸들러)
- 점검: `php/src/`, `db/` 는 건드리지 않는다 (구 UI가 현재 schema를 지원해야 함).

**예상 시간**: 5~10분 (파일 복원 + asset 캐시 무효화).

### 2.2 UI + Schema 롤백

**상황**: UI와 schema가 함께 업데이트되었고, 불완전한 마이그레이션 또는 
호환성 문제로 오류가 난다.
- 예: 새 schema에 새 컬럼이 추가되었는데, 구 UI가 그 컬럼을 읽으면서 오류가 난다.
- 예: 마이그레이션이 부분 적용되어, 일부 행은 새 컬럼이 있고 일부는 없다.
- 예: 새 schema는 적용되었지만, `php/` 코드가 새 데이터 형식을 처리하지 못한다.

**롤백 범위**:
- `php/` 전체 (UI + application code)
- `db/migrations/` 또는 DB 자체 (schema 롤백)
- **주의**: schema 롤백은 **데이터 손실 위험**이 있다. 신중히 결정해야 한다.

**예상 시간**: 30분~수시간 (schema 롤백의 복잡도에 따라).

### 2.3 부분 롤백 (선택적)

**상황**: 특정 기능만 오류가 나고, 다른 기능은 정상인 경우.
- 예: 문서 검색 기능만 500 에러가 난다.
- 예: 로그인은 작동하지만 문서 편집이 실패한다.

**롤백 범위**:
- 오류가 난 핸들러/템플릿만 구 버전으로 복원
- 나머지는 새 버전 유지
- 점검: 부분 롤백은 일관성 오류가 발생할 수 있으므로, 충분한 테스트 후 진행.

**예상 시간**: 10~15분.

**결정 기준**:
```
┌─────────────────────────────────────────┐
│ 오류 범위 평가                          │
└─────────────────────────────────────────┘
│
├─ 전체 사이트 오류 (500 on /, /docs 등)
│  └─→ "UI + Schema 함께 변경됨?" 확인
│      ├─ YES → UI + Schema 롤백
│      └─ NO  → UI만 롤백
│
├─ 특정 페이지만 오류 (/search, /docs/x)
│  └─→ 그 페이지의 핸들러/템플릿만 롤백 (부분 롤백)
│      또는 UI 전체 롤백 (더 안전)
│
├─ asset 로드 오류 (404 CSS/JS)
│  └─→ asset 파일/경로 확인 후
│      ├─ 파일 누락 → 파일 복원
│      └─ 캐시 문제 → asset 버전 무효화
│
└─ HTML/JavaScript 오류 (console error)
   └─→ 해당 템플릿/script 수정 또는
       전체 UI 롤백
```

## 3. 롤백 계획 수립 (Rollback Plan)

롤백을 실행하기 전에 계획을 문서화한다.

- [ ] **롤백할 버전 확인**: 어느 commit/tag로 롤백할 것인가?
      ```bash
      git tag -l | grep deploy
      # 또는 git log 에서 안정적인 commit 찾기
      git log --oneline | head -10
      ```

- [ ] **롤백 방법 선택**:
      - ① git revert: 새로운 commit을 만들어 변경을 되돌린다 (권장, 기록 남음)
      - ② git reset --soft: commit을 취소하고 변경사항을 staging 상태로 돌린다
      - ③ 수동 파일 복원: FTP/SSH로 파일을 직접 교체한다
      
      shared hosting 환경에서는 대부분 **③ 수동 파일 복원** 또는 
      **배포 스크립트 재실행**을 사용한다.

- [ ] **예상 영향**:
      - 롤백 중에 사이트가 온라인 상태인가, 아니면 maintenance mode로 전환하나?
      - 사용자 세션/쿠키는 유지되나?
      - 롤백 후 데이터 일관성 확인은 무엇인가?

- [ ] **복구 계획**:
      - 롤백이 실패하면? 되돌릴 수 있나?
      - 롤백 후에도 오류가 계속되면? (예: schema 문제)

- [ ] **알림 계획**:
      - 롤백을 사용자에게 알릴 것인가?
      - 예: maintenance mode 메시지 또는 공지

## 4. 롤백 실행 (Rollback Execution)

### 4.1 사전 백업

롤백 실행 직전, 현재 상태를 백업한다.

- [ ] shared hosting의 현재 `php/` 디렉터리를 백업한다.
      ```bash
      # shared hosting SSH/FTP 에서
      tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz php/
      ls -lh backup-*.tar.gz
      ```
      또는 FTP 클라이언트에서 `php/` 디렉터리 전체를 local로 다운로드.

- [ ] DB를 백업한다 (schema 롤백하는 경우).
      ```bash
      # shared hosting MySQL backup
      mysqldump -u user -p dbname > db-backup-$(date +%Y%m%d-%H%M%S).sql
      # 또는 shared hosting control panel의 backup 기능
      ```

- [ ] 백업 파일을 안전한 위치에 보관한다.
      로컬 dev 머신 또는 클라우드 스토리지.

### 4.2 UI 롤백 (파일 복원)

#### 방법 1: 배포 스크립트 재실행

배포 자동화가 있다면, 구 버전의 배포를 재실행한다.

```bash
# 로컬 dev 환경 (git repo 있음)
git checkout <stable-tag-or-commit>
# 배포 스크립트 실행
bash scripts/deploy.sh  # 또는 프로젝트의 배포 스크립트
```

#### 방법 2: 수동 파일 복원 (FTP/SSH)

shared hosting에 직접 접속하여 파일을 교체한다.

- [ ] 구 버전의 `php/public/` 파일을 준비한다 (로컬 git repo).
      ```bash
      git show <stable-commit>:php/public/ > /tmp/public_old/
      # 또는 이전 배포 tarball 에서 추출
      tar -xzf previous-deploy.tar.gz
      ```

- [ ] shared hosting에 새 파일을 업로드한다 (FTP).
      - `php/public/index.php` (front controller)
      - `php/public/assets/css/` (모든 CSS 파일)
      - `php/public/assets/js/` (모든 JavaScript 파일)
      - 기타 public assets

- [ ] `php/src/` 파일을 업로드한다 (UI 라우터/핸들러).
      ```bash
      # FTP로 업로드
      ftp> cd php/src
      ftp> mput *.php   # 변경된 핸들러/라우터
      ```

- [ ] 파일 권한을 확인한다 (644 파일, 755 디렉터리).
      ```bash
      # SSH로
      find php/public -type f -exec chmod 644 {} \;
      find php/public -type d -exec chmod 755 {} \;
      ```

### 4.3 Asset 캐시 무효화

브라우저/CDN이 여전히 이전 asset을 캐시하고 있을 수 있다. 명시적으로 무효화한다.

- [ ] asset URL의 버전 매개변수를 변경한다 (가능한 경우).
      ```php
      // php/src/Ui/AssetVersioning.php 또는 유사
      // 버전 문자열을 변경하여 모든 asset URL이 ?v=newversion 으로 변경됨
      ```

- [ ] 아니면 `php/src/Ui/` 에서 asset versioning 로직이 파일 mtime을 기반으로 한다면,
      asset 파일의 modification time을 현재 시간으로 터치한다.
      ```bash
      # shared hosting SSH에서
      touch php/public/assets/css/*.css
      touch php/public/assets/js/*.js
      # 또는
      find php/public/assets -type f -exec touch {} \;
      ```

- [ ] CDN을 사용 중이면, CDN cache를 무효화한다.
      - Cloudflare: "Purge Cache" (특정 URL 또는 전체)
      - AWS CloudFront: "Create Invalidation"
      - 기타 CDN: 제어판에서 cache purge

- [ ] PHP opcode cache를 초기화한다 (있으면).
      ```bash
      # PHP-FPM opcode cache 재시작
      # 또는 shared hosting 제어판에서 "Clear cache" 버튼 클릭
      ```

### 4.4 라우터/설정 재로드

PHP 상태를 리셋한다.

- [ ] shared hosting에서 PHP 프로세스를 재시작한다.
      - shared hosting 제어판에서 "Restart PHP" 또는
      - SSH에서 `php-fpm restart` (권한 있으면)

- [ ] 1~2분 대기하여 PHP가 완전히 재시작되도록 한다.

### 4.5 Schema 롤백 (필요한 경우만)

UI + Schema 롤백이 필요하다면, DB 마이그레이션을 되돌린다.

**⚠️ 경고**: schema 롤백은 데이터 손실을 초래할 수 있다. 매우 신중히 진행한다.

- [ ] 현재 schema 상태를 파악한다.
      ```bash
      # DB 연결 후
      SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 5;
      # 또는 직접 schema 확인
      DESCRIBE documents;
      ```

- [ ] 어느 마이그레이션까지 되돌릴 것인지 결정한다.
      ```bash
      # 로컬 git 에서
      git log --oneline -- db/migrations/ | head -10
      ```

- [ ] 마이그레이션을 되돌린다 (사용 중인 도구에 따라).
      - Laravel/similar: `php artisan migrate:rollback --step=1`
      - 수동 SQL: 마이그레이션 파일의 down() SQL을 직접 실행
      - 예:
      ```sql
      -- db/migrations/0055_add_document_visibility.sql 의 down 부분
      ALTER TABLE documents DROP COLUMN visibility;
      -- 또는
      DELETE FROM schema_migrations WHERE version = '0055_add_document_visibility';
      ```

- [ ] 롤백 후 schema 상태를 다시 확인한다.
      ```bash
      DESCRIBE documents;  # 롤백 후 컬럼 확인
      ```

## 5. 롤백 후 검증 (Post-Rollback Verification)

### 5.1 첫 페이지 렌더링

- [ ] 브라우저에서 `https://example.com/` 방문:
      - 페이지가 로드된다 (timeout/500 error 없음)
      - HTML, CSS, JavaScript가 모두 로드된다 (DevTools Network tab 확인)
      - 페이지가 스타일과 함께 렌더링된다 (blank/unstyled 페이지 아님)

- [ ] 주요 UI 요소들이 보인다:
      - header/navigation
      - main content area
      - footer

### 5.2 asset 로드 확인

- [ ] DevTools Network tab에서 모든 asset이 200 OK로 로드된다:
      ```
      /assets/css/design-tokens.css?v=...  [200]
      /assets/js/app.js?v=...              [200]
      ```

- [ ] asset 파일이 304 (Not Modified)를 반환한다면, 캐시에서 로드된 것.
      브라우저 캐시가 정상 작동하는 신호.

- [ ] console tab에 JavaScript 오류가 없다:
      - "Uncaught SyntaxError"
      - "Uncaught ReferenceError"
      - "Failed to load module script"
      등.

### 5.3 주요 기능 테스트

각 기능을 간단히 테스트하여, 롤백 후에도 작동하는지 확인한다.

- [ ] 문서 목록 보기 (`/documents/` 또는 홈): 
      - 페이지 로드 시간이 합리적인가(3초 이내)?
      - 문서 목록이 표시되는가?

- [ ] 문서 상세 보기 (`/documents/{id}`):
      - 특정 문서가 정상 렌더링되는가?
      - 콘텐츠가 올바르게 표시되는가?

- [ ] 검색 (있으면): 검색어 입력 후 결과가 표시되는가?

- [ ] 폼 제출 (있으면): 문서 생성/편집 폼이 로드되고, 제출이 가능한가?

- [ ] 오류 페이지: 존재하지 않는 페이지(`/nonexistent`)를 방문하면 
      404 페이지가 올바르게 표시되는가?

### 5.4 에러 로그 확인

- [ ] shared hosting의 error log에서 새로운 오류가 발생하지 않는지 확인한다.
      ```bash
      tail -50 /path/to/php_error.log
      # 최근 50줄에 "Fatal error", "Parse error" 등이 없어야 함
      ```

- [ ] 특히 다음 오류가 없는지 확인:
      - "Class not found": UI 파일 누락
      - "Method not found": 라우터 불일치
      - "Call to undefined function": 함수 누락

### 5.5 캐시 헤더 검증

- [ ] HTML 응답 헤더에 캐시 정책이 있다:
      ```
      Request: https://example.com/documents/page
      Response Headers:
      Cache-Control: no-cache, no-store, must-revalidate
      ```

- [ ] CSS/JS 응답 헤더에 캐시 정책이 있다:
      ```
      Cache-Control: public, max-age=31536000, immutable
      ```

### 5.6 보안 헤더 확인

- [ ] HTML 응답이 보안 헤더를 포함한다:
      ```
      X-Content-Type-Options: nosniff
      X-Frame-Options: DENY
      Content-Security-Policy: default-src 'self'
      ```

- [ ] 브라우저 콘솔에 CSP 위반 경고가 없다.

## 6. 롤백 후 지속적 모니터링 (Post-Rollback Monitoring)

### 6.1 에러 로그 모니터링 (1시간)

- [ ] 롤백 직후 1시간 동안 error log를 주시한다.
      ```bash
      # shared hosting에서 30초마다 확인
      tail -10 /path/to/php_error.log
      ```

- [ ] 특히 다음을 감시:
      - PHP Fatal error (새로운 오류)
      - Database connection error (schema 불일치)
      - Undefined variable/function (코드 불일치)

### 6.2 사용자 피드백 (4시간)

- [ ] 관리자/사용자에게 상태를 알린다:
      - "오류를 감지하여 안정적인 버전으로 롤백했습니다"
      - "현재 모든 기능이 정상 작동 중입니다"

- [ ] 사용자들이 추가 오류를 보고하지 않는지 확인한다.

### 6.3 자동 health check (계속)

- [ ] 정기적인 health check 스크립트를 실행한다:
      ```bash
      # 5분마다 실행
      curl -I https://example.com/
      curl -I https://example.com/documents/
      curl -I https://example.com/assets/css/design-tokens.css
      # HTTP status 200 확인
      ```

### 6.4 성능 기준 확인

- [ ] 첫 페이지 로드 시간이 롤백 전과 비교하여 회복했는가?
      DevTools Performance tab 또는 Lighthouse에서 측정.

- [ ] asset 로드 시간이 정상인가?

## 7. 롤백 후 근본 원인 분석 (RCA)

### 7.1 배포된 변경사항 검토

- [ ] 배포된 커밋/PR을 다시 검토한다:
      ```bash
      git log <stable-commit>..<new-commit> --oneline
      git diff <stable-commit>..<new-commit> --stat
      ```

- [ ] 오류의 근본 원인을 파악한다:
      - 누락된 파일?
      - schema 미마이그레이션?
      - 하드코딩된 경로?
      - 버전 불일치?

### 7.2 테스트 개선

- [ ] 이 오류를 감지하지 못한 이유는?
      - 로컬 테스트에서 재현되지 않았나?
      - CI/CD에서 검증이 부족했나?

- [ ] 향후 유사 오류를 방지하기 위해 테스트를 추가한다:
      ```bash
      scripts/test.sh  # UI 템플릿 테스트
      scripts/qa.sh    # HTML escaping, security headers
      ```

### 7.3 배포 프로세스 개선

- [ ] 배포 전 체크리스트를 보강한다:
      - schema/UI 호환성 확인 단계 추가
      - 로컬 smoke test 필수화
      - asset 버전 업데이트 검증

- [ ] shared hosting 환경에서 pre-deployment test를 추가한다:
      - staging 사이트에서 배포 리허설

## 8. 이 체크리스트가 다루지 않는 것

- 데이터 복구 (Data Recovery): schema 롤백으로 인한 데이터 손실 — 별도의 DB recovery strategy 참고
- Database schema 설계 문제 — schema design phase 참고
- 대규모 배포 자동화 (CI/CD 파이프라인 구성) — Phase E 배포 자동화
- 성능 최적화나 용량 계획 — performance tuning phase
- 운영 alert/모니터링 시스템 — infrastructure/DevOps phase

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — Phase D UI 아키텍처
- [PHP UI Deployment Checklist](php-ui-deployment-checklist.md) — 배포 절차 (0608)
- [PHP Static Asset Serving](php-static-asset-serving.md) — asset 배포 위치와 웹 서버 설정
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — 캐시 정책
- [PHP UI Static Asset Integrity Policy](php-ui-static-asset-integrity.md) — 버전/해시 기반 캐시 무효화
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 전체 배포 환경 정책
- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — shared hosting 환경 제약
- [PHP Runtime Phase QA Checklist](php-runtime-phase-qa-checklist.md) — Phase B QA
- [DB Phase QA Checklist](db-phase-qa-checklist.md) — Phase C QA
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) — Phase D(0521-0610) 전체 태스크 목록
