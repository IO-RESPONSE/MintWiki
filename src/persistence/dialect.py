"""SQL dialect abstraction skeleton.

docs/ansi-sql-persistence-policy.md 의 0450 항목이 예고한 대로, DB별 분기가
불가피한 지점(예: upsert)을 모아 둘 자리를 만든다. 지금은 placeholder이며
실제 방언별 SQL 생성 로직은 이후 태스크(0472 DB driver capability model
등)가 채운다 — 이 모듈은 ORM 동작을 확장하지 않는다.
"""

from abc import ABC, abstractmethod
from enum import Enum


class SqlDialect(str, Enum):
    """지원 대상 SQL dialect.

    docs/mariadb-compatibility-matrix.md 가 확정한 지원 버전과 대응한다.
    """

    POSTGRESQL = "postgresql"
    MARIADB = "mariadb"


class DialectStrategy(ABC):
    """dialect별로 분기가 필요한 동작의 skeleton.

    upsert처럼 DB마다 SQL 문법이 다른 지점을 이 인터페이스 뒤로 모은다.
    구체 구현체(PostgreSQL/MariaDB)는 이후 태스크에서 추가되며, 여기서는
    자리와 계약만 고정한다.
    """

    dialect: SqlDialect

    @abstractmethod
    def upsert_statement(self, table: object, values: dict, conflict_columns: list) -> object:
        """DB별 upsert(insert-or-update) 문을 생성한다.

        Args:
            table: 대상 ORM 테이블/매핑
            values: 삽입/갱신할 컬럼-값 매핑
            conflict_columns: 충돌 판정에 쓰이는 컬럼 목록(주로 PK/unique)

        Returns:
            실행 가능한 statement 객체

        Raises:
            NotImplementedError: 구체 dialect 구현체가 채우기 전까지는 항상
                발생한다(placeholder).
        """
        raise NotImplementedError
