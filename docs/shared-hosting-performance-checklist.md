# Shared Hosting Performance Checklist

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅 배포 전후에 확인해야 하는 최소 성능 체크리스트를 정의한다.
이 문서는 배포자가 호스팅 패널과 애플리케이션 설정에서 바로 확인할 수 있는
opcode cache, static cache, DB index 항목만 다룬다.

## 목적과 범위

- **대상**: 공용 웹호스팅 배포 담당자, installer QA 담당자, 운영 점검 담당자.
- **다루는 것**:
  - PHP opcode cache 활성화와 배포 후 갱신 확인.
  - 정적 asset 캐시 헤더와 버전 갱신 확인.
  - 핵심 조회 경로에 필요한 DB index 확인.
- **다루지 않는 것**:
  - CDN, reverse proxy, 별도 cache server 같은 외부 인프라 튜닝.
  - 코드 수준 성능 리팩터링.
  - 호스팅사별 제어판 화면 절차.

## 1. Opcode Cache 체크리스트

shared hosting에서는 PHP-FPM 또는 CGI 프로세스가 재시작되지 않아도 새 배포가
반영되어야 한다. OPcache가 제공되면 켜되, 파일 변경 감지와 배포 후 캐시 갱신
경로를 함께 확인한다.

- [ ] 호스팅 PHP 설정에서 `opcache.enable=1` 또는 동등한 OPcache 활성화 상태를 확인했다.
- [ ] CLI로 배포 스크립트를 실행하는 환경이면 `opcache.enable_cli=0`을 기본값으로 둔다.
- [ ] `opcache.validate_timestamps=1`과 짧은 `opcache.revalidate_freq`가 적용되어 파일 업로드 후 변경이 감지된다.
- [ ] 호스팅 패널 또는 PHP 런타임에서 OPcache reset 기능이 있으면 배포 절차에 포함했다.
- [ ] OPcache reset이 불가능한 호스팅에서는 파일명 또는 asset version 갱신으로 stale PHP 파일과 static asset을 구분해 진단한다.
- [ ] 배포 직후 installer 또는 운영 진단 화면에서 현재 PHP 파일의 version/build marker가 새 값인지 확인했다.

## 2. Static Cache 체크리스트

정적 asset은 웹 서버가 `php/public/assets/`에서 직접 제공한다. PHP front
controller를 통과시키지 않고, HTML과 다른 캐시 정책을 사용한다.

- [ ] CSS, JavaScript, 이미지 요청은 실제 파일로 존재할 때 rewrite를 우회해 웹 서버가 직접 응답한다.
- [ ] 해시 또는 version query가 붙은 asset은 긴 캐시(`Cache-Control: public`)를 사용할 수 있다.
- [ ] 해시 없는 asset은 짧은 캐시 또는 재검증 가능한 캐시로 운영해 배포 후 stale CSS/JS를 줄인다.
- [ ] HTML 응답은 static cache 대상이 아니며, `no-cache` 계열 정책으로 최신 문서를 확인한다.
- [ ] asset URL의 version 값은 배포 패키지 또는 manifest 변경과 함께 갱신된다.
- [ ] 배포 후 브라우저 강제 새로고침 없이도 새 CSS/JS가 내려오는지 대표 페이지에서 확인했다.

## 3. DB Index 체크리스트

shared hosting DB는 CPU와 I/O 여유가 작으므로, 자주 쓰는 목록과 단건 조회는
schema에 정의된 index를 전제로 운영한다. 누락된 index를 운영 중 임의로 추가하지
말고 migration과 schema 문서에 반영한다.

- [ ] 문서 제목, slug, namespace 같은 단건 조회 키에 unique 또는 lookup index가 있다.
- [ ] 최근 변경 목록은 revision 작성 시간과 문서 ID 기준 index를 사용한다.
- [ ] 로그인과 세션 확인 경로는 account identifier와 session token lookup index를 사용한다.
- [ ] discussion thread와 comment 목록은 document ID, thread ID, created timestamp 기준 index를 사용한다.
- [ ] job polling runner는 status, available_at, priority 같은 대기열 조회 index를 사용한다.
- [ ] 검색 기능은 shared hosting 기본 DB에서 가능한 `LIKE` 정책 범위 안에서만 동작하며, full-text 전용 index를 필수 조건으로 두지 않는다.
- [ ] schema 변경 후 `EXPLAIN`으로 대표 목록 조회가 full table scan으로 고정되지 않는지 확인했다.

## 4. 배포 전 최종 확인

- [ ] OPcache 활성화 상태와 파일 변경 감지 설정을 확인했다.
- [ ] 배포 후 OPcache reset 또는 build marker 확인 절차를 수행했다.
- [ ] 정적 asset이 `php/public/assets/`에서 웹 서버 직접 제공으로 응답한다.
- [ ] HTML과 정적 asset 캐시 정책이 서로 다르게 적용된다.
- [ ] 핵심 조회 경로의 DB index가 schema와 실제 DB에 모두 존재한다.
- [ ] 대표 조회에 대해 `EXPLAIN` 또는 호스팅 DB 도구로 index 사용 여부를 확인했다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — shared hosting 런타임 기준.
- [PHP Static Asset Serving](php-static-asset-serving.md) — 정적 asset 직접 제공 기준.
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — HTML과 정적 asset 캐시 구분.
- [PHP UI Performance Budget](php-ui-performance-budget.md) — UI 응답과 asset 크기 예산.
- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — shared hosting DB 제약.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — schema 변경 운영 기준.
