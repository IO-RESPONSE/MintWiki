# 0030 Add Current Revision Read Model

## Goal

Add a service read model that returns document metadata plus current source.

## Scope

- `src/modules/document/service.py`
- `tests/modules/document/test_service.py`

## Acceptance Criteria

- Service can return title, document id, revision id, and current source.
- Missing current revision is handled explicitly.
- Tests verify the read model.

## Out of Scope

- Rendering source to HTML.
- Search indexing.
- Database persistence.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

