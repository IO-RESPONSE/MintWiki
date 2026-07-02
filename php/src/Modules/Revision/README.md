# php/src/Modules/Revision

Revision 모듈의 SQL 저장소 구현 (태스크 0488).

- `Revision.php` (0488) — Revision 도메인 모델. 리비전 엔티티의 불변 속성
  (id, document_id, source, author_id, summary, parent_revision_id)을 표현한다.
- `RevisionRepository.php` (0488) — Revision SQL 저장소 skeleton. 
  `PdoTransaction`을 감싸서 create/get/list_by_document_id 
  operations를 노출한다. 지금은 placeholder SQL을 사용하며, 
  실제 쿼리 구현은 이후 태스크에서 추가된다.

## Placeholder SQL

이 단계에서 SQL은 아직 구현되지 않았다. 저장소 골격과 테스트 구조만 
확정되었으며, 다음 태스크에서 실제 INSERT/SELECT/UPDATE 문이 추가된다.

## List Ordering Contract

`listByDocumentId()` 메서드는 다음 계약을 만족한다:

- 결과는 `created_at` 기준 **오름차순**으로 정렬된다 (가장 오래된 것부터).
- 이 순서는 편집 이력을 시간순으로 추적하기 위해 필수이다.
- 빈 배열을 반환할 수 있다 (문서에 리비전이 없음).

## References

- `docs/db-adapter-contract.md` — Repository 계약과 세션 소유권
- `docs/persistence-boundaries.md` — Revision 모듈의 책임과 불변식
