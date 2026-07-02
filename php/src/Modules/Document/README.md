# php/src/Modules/Document

Document 모듈의 SQL 저장소 구현 (태스크 0487).

- `Document.php` (0487) — Document 도메인 모델. 문서 엔티티의 불변 속성
  (id, title, normalized_title, current_revision_id)을 표현한다.
- `DocumentRepository.php` (0487) — Document SQL 저장소 skeleton. 
  `PdoTransaction`을 감싸서 create/get/get_by_normalized_title/update 
  operations를 노출한다. 지금은 placeholder SQL을 사용하며, 
  실제 쿼리 구현은 이후 태스크에서 추가된다.

## Placeholder SQL

이 단계에서 SQL은 아직 구현되지 않았다. 저장소 골격과 테스트 구조만 
확정되었으며, 다음 태스크에서 실제 INSERT/SELECT/UPDATE 문이 추가된다.

## References

- `docs/db-adapter-contract.md` — Repository 계약과 세션 소유권
- `docs/persistence-boundaries.md` — Document 모듈의 책임과 불변식
