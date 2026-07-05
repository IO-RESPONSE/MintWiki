# 0709 Edit toolbar and markup help

## Goal

편집 화면에 NamuMark 문법 삽입 툴바와 접이식 문법 도움말(치트시트)을 추가해 초심자도 문법을 쉽게 쓰게 한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Ui/DocumentEditorPage.php (툴바 + 도움말 마크업)
- php/public/assets (툴바 JS/CSS, 점진적 향상)
- php/tests

## Acceptance Criteria

- 편집기 상단에 툴바 버튼을 추가한다: 굵게(`'''`), 기울임(`''`), 밑줄(`__`), 링크(`[[ ]]`), 제목(`== ==`), 목록(`* `), 표(`|| ||`). 클릭 시 textarea 선택 영역에 해당 문법을 감싸/삽입한다.
- **점진적 향상**: 툴바는 assets/js로 동작하고, JS가 없어도 편집·저장은 정상. 툴바 버튼은 접근성(aria-label, 키보드 포커스)을 갖춘다.
- 접이식 "문법 도움말" 패널을 추가해 주요 NamuMark 문법 예시(입력→결과)를 보여준다. 순수 HTML/CSS(`<details>` 등)로 JS 없이도 펼쳐진다.
- 툴바/도움말의 모든 텍스트는 이스케이프되고, 스킨 브랜드 토큰으로 스타일링한다.
- php 테스트로 편집 화면에 툴바 컨트롤과 도움말 패널 마크업이 존재하고, 각 버튼이 대응 문법 데이터 속성을 갖는지 검증한다.

## Out of Scope

- 미리보기(0708) — 별개.
- 위지윅.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`DocumentEditorPage`에 통합. 외부 라이브러리 금지(self-contained 배포) — 툴바 JS는 인라인/assets 최소 구현. `<details>/<summary>`로 no-JS 도움말 제공.
