# 0716 Backup direct download

## Goal

관리자가 백업 파일을 브라우저에서 바로 내려받을 수 있게 다운로드 라우트를 추가하고, 백업 목록의 각 항목에 다운로드 링크를 노출한다. 현재는 목록만 보이고 다운로드 수단이 없다.

## Phase

Phase K: Delete + audit logging + backup download, 0714+.

## Scope

- php/public/index.php (다운로드 라우트)
- php/src/Ui/BackupPage.php (목록에 다운로드 링크)
- php/src/Admin (FileBackupRunner에 안전한 파일 경로 해석 헬퍼 필요 시)
- php/tests

## Acceptance Criteria

- `GET /admin/backup/download?name={파일명}`(또는 `/admin/backup/download/{name}`)을 등록한다 — 0696 관리자 게이트로 보호하고, `storage/backups/`의 해당 파일을 적절한 헤더(`Content-Type: application/octet-stream` 또는 json, `Content-Disposition: attachment; filename=...`, `Content-Length`)와 함께 스트리밍한다.
- **경로 traversal 방지**: `name`은 basename만 허용하고(`/`·`..` 거부), `FileBackupRunner`가 나열하는 실제 백업 파일 집합(정규식 `\.(json|sql)$`)에 속한 항목만 내려준다. 목록에 없는/존재하지 않는 파일은 404.
- `BackupPage`가 각 백업 항목 옆에 "다운로드" 링크(위 라우트로)를 렌더한다. 파일명은 `Escaper`로 이스케이프.
- 대용량이어도 메모리 폭주 없이 스트리밍한다(`readfile`/청크). 다운로드 동작을 감사 이벤트로 기록한다(0714, 선택).
- php 테스트로 (1) 유효 파일 다운로드가 올바른 헤더+본문 반환, (2) traversal/미존재/목록외 파일 거부(404/403), (3) 관리자 게이트(익명 302/비관리자 403), (4) 목록에 다운로드 링크 노출을 검증한다.

## Out of Scope

- 백업 삭제·업로드(복원은 기존 0701 restore).
- 원격 스토리지 연동.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`FileBackupRunner`는 `storage_path/backups`에 `mintwiki-backup-*.json`을 저장하고 `listBackups()`로 나열한다(`StoragePathConfig` 기준). 다운로드는 반드시 `listBackups()` 화이트리스트로 검증해 임의 파일 노출을 막는다. `.sql` 확장자는 호스팅 WAF가 막을 수 있으나 백업은 `.json`이라 무관.
