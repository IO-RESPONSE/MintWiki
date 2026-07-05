# 0703 Add Write Entrypoint

## Goal

배포된 MintWiki 화면에서 사용자가 새 문서 작성 화면으로 들어갈 수 있는 명확한 글쓰기 진입점을 추가한다.

## Scope

- `php/public/index.php`
- `php/src/Ui/NavigationBar.php` 또는 navigation wiring
- `php/tests/Http/*`

## Acceptance Criteria

- 상단 네비게이션에 "글쓰기" 링크가 노출되고 `/write`로 이동한다.
- `GET /write`가 새 문서 작성 폼을 반환한다.
- 작성 저장은 기존 `/wiki/{title}/edit` 생성/리비전 저장 경로를 재사용한다.
- Automated tests pass.

## Out of Scope

- WYSIWYG/Markdown 편집기 고도화.
- 문서 작성 권한 정책 변경.
- 배포 서버 반영 및 운영 계정 생성.

## QA

- `php/scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 `GET/POST /wiki/{title}/edit`가 생성과 편집을 모두 처리한다. 이번 작업은 배포 화면에서 찾을 수 있는 작성 진입점만 얇게 연결한다.
