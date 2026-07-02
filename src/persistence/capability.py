"""DB driver capability model.

docs/db-adapter-contract.md §0472가 예고한 대로, 어댑터가 드라이버별로
다르게 노출할 수 있는 기능 차이(삽입 직후 결과 행을 곧바로 돌려주는 절의
지원 여부 등)를 값 객체로 표현한다. docs/mariadb-compatibility-matrix.md가
확정한 차이를 코드로 옮길 뿐 새 정책을 만들지 않는다 — 실제 방언별 SQL
생성 로직은 dialect.py의 DialectStrategy가 이후 태스크에서 채운다.
"""

from dataclasses import dataclass

from persistence.dialect import SqlDialect


@dataclass(frozen=True)
class DriverCapabilities:
    """단일 dialect가 네이티브로 지원하는 기능 플래그 모음.

    Attributes:
        supports_returning: `INSERT`/`UPDATE`/`DELETE` 직후 결과 행을
            별도 재조회 없이 곧바로 돌려주는 절(docs/db-adapter-contract.md
            §0472 참고)을 표준 지원하는지 여부.
        supports_json: 네이티브 JSON 타입과 질의 연산자(`->`, `->>` 등)를
            지원하는지 여부. MariaDB의 `JSON`은 `LONGTEXT` 별칭이라
            연산자가 없으므로 False다.
        supports_fulltext: 네이티브 전문 검색 인덱스/질의를 지원하는지
            여부. search 모듈은 이 플래그와 무관하게 엔진 비종속
            어댑터 뒤로 검색을 숨긴다(docs/search-adapter-design.md).
    """

    dialect: SqlDialect
    supports_returning: bool
    supports_json: bool
    supports_fulltext: bool


_CAPABILITIES: dict[SqlDialect, DriverCapabilities] = {
    SqlDialect.POSTGRESQL: DriverCapabilities(
        dialect=SqlDialect.POSTGRESQL,
        supports_returning=True,
        supports_json=True,
        supports_fulltext=True,
    ),
    SqlDialect.MARIADB: DriverCapabilities(
        dialect=SqlDialect.MARIADB,
        supports_returning=False,
        supports_json=False,
        supports_fulltext=False,
    ),
}


def capabilities_for(dialect: SqlDialect) -> DriverCapabilities:
    """dialect에 대응하는 DriverCapabilities를 반환한다.

    Args:
        dialect: 조회할 SQL dialect.

    Returns:
        해당 dialect의 기능 플래그 모음.

    Raises:
        KeyError: 등록되지 않은 dialect가 주어진 경우.
    """
    return _CAPABILITIES[dialect]
