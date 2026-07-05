# 0707 Edit summary (change reason) field

## Goal

편집/글쓰기 저장 시 "편집 요약(변경 이유)"을 입력받아 리비전에 기록하고, 역사(history)에서 각 리비전의 요약을 볼 수 있게 한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Ui/DocumentEditorPage.php (요약 입력 필드)
- php/public/index.php (POST /wiki/{title}/edit, /write 저장 경로에서 summary 수집·전달)
- php/src/Ui/DocumentHistoryPage.php (요약 표시, 0710과 정합)
- php/tests

## Acceptance Criteria

- `DocumentEditorPage`에 "편집 요약" 입력 필드(짧은 텍스트, 선택 또는 필수는 기존 UX 관례에 맞게)를 추가하고, 편집/새문서 폼 모두에 노출한다. `render()`에 summary 파라미터를 더해 검증 실패 시 값이 유지되게 한다.
- `POST /wiki/{title}/edit`와 `/write` 저장 처리에서 폼의 summary를 읽어 새 `Revision`의 `summary`로 저장한다. 빈 값 정책(예: 빈 요약 허용 시 기본 문자열, 500자 초과 시 잘라내기/검증)을 명시적으로 처리한다.
- 요약 텍스트는 저장·표시 모두에서 `Escaper`로 이스케이프한다(XSS).
- `DocumentHistoryPage`가 각 리비전의 요약을 표시하도록 데이터 계약을 맞춘다(실제 라우트 배선은 0710, 이 태스크는 표시 필드가 요약을 받도록 준비).
- php 테스트로 (1) 폼에 요약 필드 존재·값 유지, (2) 저장 시 Revision.summary에 반영, (3) 길이/빈값 경계, (4) 이스케이프를 검증한다.

## Out of Scope

- history 라우트 자체(0710).
- 미리보기(0708).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`revision` 스키마에 `summary VARCHAR(500) NOT NULL` **이미 존재** — 스키마 변경 불필요, 저장 경로가 실제 값을 넣도록만 하면 됨. 현재 `DocumentEditorPage.render`는 summary 파라미터가 없고 폼에 필드도 없다. `Revision\PdoRepository.create()`가 summary를 이미 기록하므로 값 전달만 배선.
