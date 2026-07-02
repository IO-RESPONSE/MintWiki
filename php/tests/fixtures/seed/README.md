# Seed Fixtures

Portable seed fixture 파일들. ANSI SQL 기반 INSERT 문으로 구성되며, PostgreSQL과 MariaDB에서 동일하게 동작한다.

## 파일들

- `documents.sql` — 3개의 기본 문서 데이터
- `revisions.sql` — 4개의 리비전 데이터

FK 종속성을 고려하여 파일명이 알파벳 순서로 정렬되므로, `loadAllSeeds()` 호출 시 documents가 먼저 로드되고 revisions이 나중에 로드된다.
